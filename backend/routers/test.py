"""
test.py – Function-test endpoints.

/api/test/token
  Connects to a locally running Chrome instance via the Chrome DevTools Protocol
  (CDP), finds the target tab by URL, and reads a JWT token from its
  localStorage.  No client-side Chrome Extension is needed.

  If Chrome is not already running with --remote-debugging-port=9222, this
  endpoint will launch it automatically and open the target site in a new tab.
"""

import asyncio
import json
import platform
import re
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt as _jwt

import requests as _requests
import websockets
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from backend.data_conversion import (
    convert_task_details,
    convert_pagination_response,
    convert_task_list_response,
)

router = APIRouter()

# ── Configuration ──────────────────────────────────────────────────────────────
CDP_HTTP = "http://localhost:9222"  # Chrome DevTools HTTP endpoint
TARGET_URL = "https://101-next.orbitfin.ai"  # site to open / find
TARGET_URL_CONTAINS = "101-next.orbitfin.ai"  # substring to match the tab
JWT_TOKEN_STORAGE_KEY = "jwt_token"  # localStorage key holding the JWT
REFRESH_TOKEN_STORAGE_KEY = (
    "refresh_token"  # localStorage key holding the refresh token
)
TASK_LIST_API_URL = (
    "https://101-next.orbitfin.ai/prod/security/task/list"  # task list endpoint
)
ASSIGN_TASK_API_URL = (
    "https://101-next.orbitfin.ai/prod/security/task/assign"  # assign task endpoint
)
ABANDON_TASK_API_URL = (
    "https://101-next.orbitfin.ai/prod/security/task/abandon"  # abandon task endpoint
)
REFRESH_TOKEN_API_URL = (
    "https://101-next.orbitfin.ai/prod/login/refresh"  # refresh token endpoint
)
TASK_DETAIL_API_URL = (
    "https://101-next.orbitfin.ai/prod/security/task/detail"  # task detail endpoint
)
TASK_DETAIL_ENRICH_IDS = {2017, 2018}
# ──────────────────────────────────────────────────────────────────────────────

# ── Chrome launch helpers ──────────────────────────────────────────────────────


def _chrome_executable() -> str:
    """Return the path to the Chrome binary for the current OS."""
    system = platform.system()
    if system == "Darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if system == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for c in candidates:
            if shutil.which(c):
                return c
        return "chrome"
    # Linux
    for name in (
        "google-chrome",
        "google-chrome-stable",
        "chromium-browser",
        "chromium",
    ):
        found = shutil.which(name)
        if found:
            return found
    return "google-chrome"


def _launch_chrome_with_debug_port() -> None:
    """
    Start Chrome with --remote-debugging-port=9222 as a detached background
    process and return immediately (fire-and-forget).
    The caller is responsible for showing a retry message to the user.
    """
    exe = _chrome_executable()
    cmd = [
        exe,
        "--remote-debugging-port=9222",
        "--no-first-run",
        "--no-default-browser-check",
        # Use a dedicated profile dir so this instance is always a separate
        # process from any existing Chrome, guaranteeing the debug port is open.
        "--user-data-dir=/tmp/chrome-debug-profile",
        TARGET_URL,
    ]
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # detach from the server process
    )
    # Return immediately – no blocking poll.
    # The /api/test/token endpoint will return a "retry" response so the user
    # knows to wait for Chrome to finish starting up.


def _open_new_tab_via_cdp(url: str) -> None:
    """Ask a running Chrome to open *url* in a new tab via CDP REST API."""
    _requests.put(f"{CDP_HTTP}/json/new?{url}", timeout=5)


def _ensure_chrome_and_tab() -> bool:
    """
    1. If Chrome's CDP port is unreachable → launch Chrome (with the target URL).
    2. If Chrome is running but no tab matches TARGET_URL_CONTAINS → open one.

    Returns True if everything was already in place (token may be readable now).
    Returns False if Chrome/tab was just launched (caller should tell client to retry).
    """
    cdp_reachable = False
    try:
        r = _requests.get(f"{CDP_HTTP}/json", timeout=2)
        r.raise_for_status()
        tabs = r.json()
        cdp_reachable = True
    except Exception:
        tabs = []

    if not cdp_reachable:
        # Chrome is not open with the debug port – launch it
        _launch_chrome_with_debug_port()
        return False  # just launched – page is still loading

    # Chrome is running but the target tab may be missing
    has_target = any(TARGET_URL_CONTAINS in t.get("url", "") for t in tabs)
    if not has_target:
        _open_new_tab_via_cdp(TARGET_URL)
        return False  # tab just opened – page is still loading

    return True  # Chrome was already running with the target tab


# ── CDP helpers ────────────────────────────────────────────────────────────────


async def _wait_for_tab(timeout: int = 35) -> bool:
    """
    Poll the CDP /json endpoint until the target tab URL appears, or until
    *timeout* seconds have elapsed.  Returns True when the tab is found.
    """
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            r = await asyncio.to_thread(
                lambda: _requests.get(f"{CDP_HTTP}/json", timeout=2)
            )
            r.raise_for_status()
            tabs = r.json()
            if any(TARGET_URL_CONTAINS in t.get("url", "") for t in tabs):
                return True
        except Exception:
            pass
        await asyncio.sleep(1)
    return False


async def _wait_for_localStorage_token(ws_url: str, timeout: int = 60) -> str | None:
    """
    Poll localStorage.getItem(TOKEN_STORAGE_KEY) via CDP every second until
    a non-null value appears or *timeout* seconds elapse.

    This is more reliable than waiting for document.readyState because SPAs
    write to localStorage *after* the page is 'complete' (once the auth API
    call returns), so readyState 'complete' fires too early.

    Returns the token string, or None if it never appeared within timeout.
    """
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            jwt_token = await _cdp_eval(
                ws_url,
                1,
                f"localStorage.getItem({json.dumps(JWT_TOKEN_STORAGE_KEY)})",
            )
            value = jwt_token.get("result", {}).get("result", {}).get("value")
            if value is not None:
                return value
        except Exception:
            pass
        await asyncio.sleep(1)
    return None


async def _read_both_tokens(ws_url: str) -> tuple[str | None, str | None]:
    """Read both the JWT token and the refresh token from localStorage in one go."""
    try:
        jwt_result = await _cdp_eval(
            ws_url, 1, f"localStorage.getItem({json.dumps(JWT_TOKEN_STORAGE_KEY)})"
        )
        refresh_result = await _cdp_eval(
            ws_url, 2, f"localStorage.getItem({json.dumps(REFRESH_TOKEN_STORAGE_KEY)})"
        )
        jwt_value = jwt_result.get("result", {}).get("result", {}).get("value")
        refresh_value = refresh_result.get("result", {}).get("result", {}).get("value")
        return jwt_value, refresh_value
    except Exception:
        return None, None


async def _cdp_eval(ws_url: str, msg_id: int, expression: str) -> dict:
    """Open a CDP WebSocket, send a Runtime.evaluate command, return the result."""
    async with websockets.connect(ws_url, open_timeout=5) as ws:
        cmd = json.dumps(
            {
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": expression,
                    "returnByValue": True,
                },
            }
        )
        await ws.send(cmd)
        raw = await ws.recv()
    return json.loads(raw)


@router.post("/token")
async def token_auto_test():
    # 1. Ensure Chrome is running with CDP and the target tab is open
    try:
        tab_was_ready = await asyncio.to_thread(_ensure_chrome_and_tab)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to launch or connect to Chrome: {exc}",
        )

    # Track whether we just launched Chrome/tab so we know to wait for page load
    tab_just_launched = not tab_was_ready

    if tab_just_launched:
        # Chrome or the tab was just launched – poll until the tab URL appears
        # in CDP (up to 35 s).
        tab_was_ready = await _wait_for_tab(timeout=35)

        if not tab_was_ready:
            return {
                "success": False,
                "retry": True,
                "detail": (
                    f"Chrome / target tab was just opened at {TARGET_URL}. "
                    "Please wait for the page to finish loading and log in, "
                    "then click the button again."
                ),
            }
        # Tab is now accessible – fall through to read the token.

    # 2. List all open Chrome tabs via CDP HTTP API
    try:
        resp = _requests.get(f"{CDP_HTTP}/json", timeout=5)
        resp.raise_for_status()
        tabs = resp.json()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot reach Chrome DevTools at {CDP_HTTP}: {exc}",
        )

    # 3. Find the target tab
    target = next((t for t in tabs if TARGET_URL_CONTAINS in t.get("url", "")), None)
    if not target:
        open_urls = [t.get("url") for t in tabs]
        raise HTTPException(
            status_code=404,
            detail=(
                f"No tab found with URL containing '{TARGET_URL_CONTAINS}' "
                f"even after attempting to open one. Open tabs: {open_urls}"
            ),
        )

    ws_url = target.get("webSocketDebuggerUrl")
    if not ws_url:
        raise HTTPException(
            status_code=502,
            detail="Target tab has no webSocketDebuggerUrl (it may already be attached to another DevTools session).",
        )

    # 4. If the tab was just launched, poll localStorage directly until the
    #    token key appears (the SPA writes it after its auth API call returns,
    #    which is long after document.readyState becomes 'complete').
    if tab_just_launched:
        token_value = await _wait_for_localStorage_token(ws_url, timeout=60)
        if token_value is None:
            return {
                "success": False,
                "retry": True,
                "detail": (
                    f"Tab at {target['url']} loaded but '{JWT_TOKEN_STORAGE_KEY}' "
                    "was not found in localStorage after 60 s. "
                    "Please log in and click the button again."
                ),
            }
        # Also grab the refresh token now that the page has finished auth
        _, refresh_value = await _read_both_tokens(ws_url)
        return {
            "success": True,
            "tab_url": target["url"],
            "jwt_token_storage_key": JWT_TOKEN_STORAGE_KEY,
            "jwt_token_value": token_value,
            "refresh_token_storage_key": REFRESH_TOKEN_STORAGE_KEY,
            "refresh_token_value": refresh_value,
        }

    # 5. Read the token from localStorage via CDP (tab was already open)
    try:
        jwt_token_result = await _cdp_eval(
            ws_url,
            1,
            f"localStorage.getItem({json.dumps(JWT_TOKEN_STORAGE_KEY)})",
        )

        refresh_token_result = await _cdp_eval(
            ws_url,
            1,
            f"localStorage.getItem({json.dumps(REFRESH_TOKEN_STORAGE_KEY)})",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"CDP WebSocket error: {exc}",
        )

    jwt_token_value = jwt_token_result.get("result", {}).get("result", {}).get("value")
    refresh_token_value = (
        refresh_token_result.get("result", {}).get("result", {}).get("value")
    )

    if jwt_token_value is None or refresh_token_value is None:
        # Retrieve available keys to help diagnose the wrong key name
        try:
            keys_result = await _cdp_eval(
                ws_url,
                2,
                "JSON.stringify(Object.keys(localStorage))",
            )
            raw_keys = (
                keys_result.get("result", {}).get("result", {}).get("value", "[]")
            )
            available_keys = json.loads(raw_keys)
        except Exception:
            available_keys = []

        raise HTTPException(
            status_code=404,
            detail=(
                f"Key '{JWT_TOKEN_STORAGE_KEY}' or '{REFRESH_TOKEN_STORAGE_KEY}' not found in localStorage of "
                f"tab '{target['url']}'. "
                f"Available keys: {available_keys}"
            ),
        )

    return {
        "success": True,
        "tab_url": target["url"],
        "jwt_token_storage_key": JWT_TOKEN_STORAGE_KEY,
        "jwt_token_value": jwt_token_value,
        "refresh_token_storage_key": REFRESH_TOKEN_STORAGE_KEY,
        "refresh_token_value": refresh_token_value,
    }


# ── Task List endpoint ─────────────────────────────────────────────────────────


class TaskListRequest(BaseModel):
    page: int = 1
    page_size: int = 10
    view_type: str = "available"


def _fetch_task_detail(task_id: int, headers: dict[str, str]) -> dict:
    """Fetch a single task detail payload and return the decoded JSON body."""
    try:
        resp = _requests.get(
            TASK_DETAIL_API_URL,
            params={"task_id": task_id},
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
    except _requests.exceptions.ConnectionError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot connect to task detail API: {exc}",
        )
    except _requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, detail="Task detail API request timed out."
        )
    except _requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        raise HTTPException(
            status_code=status_code,
            detail=f"Task detail API returned HTTP {status_code} for task {task_id}.",
        )
    except _requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        return resp.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Task detail API returned invalid JSON for task {task_id}: {exc}",
        )


def _enrich_task_with_details(task, headers: dict[str, str]):
    """Return a new TaskInfo with detail data applied atomically."""
    task_detail_data = _fetch_task_detail(task.id, headers)
    print(f"task detail data for task {task.id}: {task_detail_data}")
    return convert_task_details(task, task_detail_data)


@router.post("/init-task-list")
def task_list(
    body: TaskListRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Fetch the task list from the target API using the supplied JWT token.
    The Authorization header must be in the format: JWT <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required (format: JWT <token>)",
        )

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    params = {
        "page": body.page,
        "page_size": body.page_size,
        "view_type": body.view_type,
    }

    try:
        resp = _requests.post(
            TASK_LIST_API_URL, headers=headers, json=params, timeout=30
        )
    except _requests.exceptions.ConnectionError as exc:
        raise HTTPException(
            status_code=502, detail=f"Cannot connect to task list API: {exc}"
        )
    except _requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Task list API request timed out.")
    except _requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        data = resp.json()

        # Convert the raw API response to a list of TaskInfo objects using the data_conversion helper
        init_tasks = convert_task_list_response(data)
        print(f"initial task list {init_tasks}")

        # Convert the raw API response to pagination info using the data_conversion helper
        pagination_info = convert_pagination_response(data)
        print(f"pagination info: {pagination_info}")

        enriched_tasks = []
        for task in init_tasks:
            enriched_tasks.append(_enrich_task_with_details(task, headers))
            # if task.id in TASK_DETAIL_ENRICH_IDS:
            #     enriched_tasks.append(_enrich_task_with_details(task, headers))
            # else:
            #     enriched_tasks.append(task)
        init_tasks = enriched_tasks

    except Exception:
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"TASK_LIST_API_URL ({TASK_LIST_API_URL}) returned HTML instead of JSON. "
                    "The URL is likely wrong — check the actual API endpoint in Chrome DevTools Network tab."
                ),
            )
        data = {"raw": resp.text}

    return {
        "success": resp.ok,
        "status_code": resp.status_code,
        "data": init_tasks,
        "pagination": pagination_info,
    }


# API Assign Task Testing
class AssignTaskRequest(BaseModel):
    task_id: int = 1927


@router.post("/assign-task")
def assign_task(
    body: AssignTaskRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Assign a task using the supplied JWT token.
    The Authorization header must be in the format: JWT <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required (format: JWT <token>)",
        )

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    params = {
        "task_id": body.task_id,
    }

    try:
        resp = _requests.post(
            ASSIGN_TASK_API_URL, headers=headers, json=params, timeout=30
        )
    except _requests.exceptions.ConnectionError as exc:
        raise HTTPException(
            status_code=502, detail=f"Cannot connect to assign task API: {exc}"
        )
    except _requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, detail="Assign task API request timed out."
        )
    except _requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        data = resp.json()
    except Exception:
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"TASK_LIST_API_URL ({TASK_LIST_API_URL}) returned HTML instead of JSON. "
                    "The URL is likely wrong — check the actual API endpoint in Chrome DevTools Network tab."
                ),
            )
        data = {"raw": resp.text}

    return {
        "success": resp.ok,
        "status_code": resp.status_code,
        "data": data,
    }


# API Abandon Task Testing
class AbandonTaskRequest(BaseModel):
    task_id: int = 1927


@router.post("/abandon-task")
def abandon_task(
    body: AbandonTaskRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Abandon a task using the supplied JWT token.
    The Authorization header must be in the format: JWT <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required (format: JWT <token>)",
        )

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    params = {
        "task_id": body.task_id,
    }

    try:
        resp = _requests.post(
            ABANDON_TASK_API_URL, headers=headers, json=params, timeout=30
        )
    except _requests.exceptions.ConnectionError as exc:
        raise HTTPException(
            status_code=502, detail=f"Cannot connect to abandon task API: {exc}"
        )
    except _requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, detail="Abandon task API request timed out."
        )
    except _requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        data = resp.json()
    except Exception:
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"TASK_LIST_API_URL ({TASK_LIST_API_URL}) returned HTML instead of JSON. "
                    "The URL is likely wrong — check the actual API endpoint in Chrome DevTools Network tab."
                ),
            )
        data = {"raw": resp.text}

    return {
        "success": resp.ok,
        "status_code": resp.status_code,
        "data": data,
    }


# Refresh Token Testing
class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh-token")
def refresh_token(
    body: RefreshTokenRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Refresh the JWT token using the supplied refresh token.
    """
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    params = {
        "refresh": body.refresh_token,
    }

    try:
        resp = _requests.post(
            REFRESH_TOKEN_API_URL, headers=headers, json=params, timeout=30
        )
    except _requests.exceptions.ConnectionError as exc:
        raise HTTPException(
            status_code=502, detail=f"Cannot connect to refresh token API: {exc}"
        )
    except _requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, detail="Refresh token API request timed out."
        )
    except _requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        data = resp.json()
    except Exception:
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"REFRESH_TOKEN_API_URL ({REFRESH_TOKEN_API_URL}) returned HTML instead of JSON. "
                    "The URL is likely wrong — check the actual API endpoint in Chrome DevTools Network tab."
                ),
            )
        data = {"raw": resp.text}

    return {
        "success": resp.ok,
        "status_code": resp.status_code,
        "data": data,
    }


# API Validate Token Testing
class ValidateTokenRequest(BaseModel):
    refreshToken: str


@router.post("/validate-token")
def validate_token(
    body: ValidateTokenRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Validate a JWT token using the Authorization header.
    The Authorization header must be in the format: JWT <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required (format: JWT <token>)",
        )

    refresh_token = body.refreshToken  # may be None/empty if not yet available
    print(
        f"Received token for validation: {authorization}, refresh token: {refresh_token}"
    )

    # decode jwt token
    # Strip the "JWT " (or "Bearer ") scheme prefix to get the raw token string
    raw_token = authorization.strip()
    for prefix in ("JWT ", "Bearer "):
        if raw_token.upper().startswith(prefix.upper()):
            raw_token = raw_token[len(prefix) :].strip()
            break

    # use regex to replace the global quote
    raw_token = re.sub(r'^"|"$', "", raw_token)

    try:
        # Decode without signature verification – we only need the payload claims
        payload = _jwt.decode(
            raw_token,
            options={"verify_signature": False},
            algorithms=["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"],
        )
    except _jwt.DecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JWT token – cannot decode: {exc}",
        )

    exp_ts: int | None = payload.get("exp")
    if exp_ts is None:
        raise HTTPException(
            status_code=400,
            detail="JWT token does not contain an 'exp' (expiration) claim.",
        )

    exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    exp_dt_plus_2 = exp_dt + timedelta(minutes=2)
    now_dt = datetime.now(timezone.utc)
    is_expired = now_dt > exp_dt_plus_2
    seconds_remaining = (exp_dt_plus_2 - now_dt).total_seconds()

    print(f"Received token for validation: {authorization}")

    new_jwt_token = raw_token
    new_refresh_token = refresh_token

    print(f"current jwt token is expired - {is_expired}")

    if is_expired:
        print(
            f"Token is expired. Expired at {exp_dt.isoformat()} (UTC), "
            f"{-seconds_remaining:.0f} seconds ago."
        )
        # need to call refresh token to get the new token

        # region Call the refresh token API to get a new token

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        params = {
            "refresh": refresh_token,
        }

        try:
            resp = _requests.post(
                REFRESH_TOKEN_API_URL, headers=headers, json=params, timeout=30
            )
            print(
                f"Called refresh token API at {REFRESH_TOKEN_API_URL} with refresh token: {refresh_token}"
            )
        except _requests.exceptions.ConnectionError as exc:
            raise HTTPException(
                status_code=502, detail=f"Cannot connect to refresh token API: {exc}"
            )
        except _requests.exceptions.Timeout:
            raise HTTPException(
                status_code=504, detail="Refresh token API request timed out."
            )
        except _requests.RequestException as exc:
            raise HTTPException(status_code=502, detail=str(exc))

        try:
            data = resp.json()
            print(f"Refresh token API response: {data}")

            new_jwt_token = data.get("data", {}).get("access")
            new_refresh_token = data.get("data", {}).get("refresh")

            print(f"New JWT token: {new_jwt_token}")
            print(f"New refresh token: {new_refresh_token}")

        except Exception:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        f"REFRESH_TOKEN_API_URL ({REFRESH_TOKEN_API_URL}) returned HTML instead of JSON. "
                        "The URL is likely wrong — check the actual API endpoint in Chrome DevTools Network tab."
                    ),
                )
            data = {"raw": resp.text}

        # endregion

    print(
        f"Returning token validation result: valid={not is_expired}, expired={is_expired}, "
        f"new_jwt_token={new_jwt_token}, new_refresh_token={new_refresh_token}"
    )

    return {
        "success": True,
        "status_code": 200,
        "data": {
            "valid": not is_expired,
            "expired": is_expired,
            "exp": exp_ts,
            "exp_utc": exp_dt.isoformat(),
            "now_utc": now_dt.isoformat(),
            "seconds_remaining": round(seconds_remaining, 0),
            "new_jwt_token": new_jwt_token,
            "new_refresh_token": new_refresh_token,
        },
    }
