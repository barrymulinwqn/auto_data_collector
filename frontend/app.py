import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def _api(path: str) -> str:
    return f"{BACKEND_URL}{path}"


@app.route("/")
def index():
    try:
        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(_api("/api/test/token"), timeout=60)
        resp.raise_for_status()
        tokens = resp.json()
        print(f"Token retrieval successful: {tokens}")
        jwt_token = tokens.get("jwt_token_value")
        refresh_token = tokens.get("refresh_token_value")
        print(f"JWT Token: {jwt_token}, Refresh Token: {refresh_token}")

        # validate if jwt_token is expired or not
        body = {
            "refreshToken": refresh_token,
        }
        headers = {}
        if jwt_token:
            headers["Authorization"] = f"JWT {jwt_token}"
            headers["Content-Type"] = "application/json"

        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(
            _api("/api/test/validate-token"),
            json=body,
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        new_tokens = resp.json()
        print(f"Token validation successful: {new_tokens}")

        new_jwt_token = new_tokens.get("data", {}).get("new_jwt_token")
        new_refresh_token = new_tokens.get("data", {}).get("new_refresh_token")
        print(f"New JWT Token: {new_jwt_token}, New Refresh Token: {new_refresh_token}")

        # get task list data
        body = {"page": 1, "page_size": 1, "view_type": "available"}
        headers = {}
        if new_jwt_token:
            headers["Authorization"] = f"JWT {new_jwt_token}"
            headers["Content-Type"] = "application/json"

        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(
            _api("/api/test/init-task-list"),
            json=body,
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        ini_task_list = resp.json()
        tasks = ini_task_list.get("data", [])
        pagination_info = {"current_page": 1}
        print(f"Initial Task List retrieval successful: {tasks}")

    except requests.RequestException:
        tasks = []
        pagination_info = {"current_page": 1}
        flash("Could not connect to backend API.", "danger")
    # return render_template("index.html", items=items)
    return render_template(
        "task_dashboard.html", tasks=tasks, pagination=pagination_info
    )


@app.route("/next-task")
def next_task():
    next_page = request.args.get("next_page", 2, type=int)
    try:
        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(_api("/api/test/token"), timeout=60)
        resp.raise_for_status()
        tokens = resp.json()
        print(f"Token retrieval successful: {tokens}")
        jwt_token = tokens.get("jwt_token_value")
        refresh_token = tokens.get("refresh_token_value")
        print(f"JWT Token: {jwt_token}, Refresh Token: {refresh_token}")

        # validate if jwt_token is expired or not
        body = {
            "refreshToken": refresh_token,
        }
        headers = {}
        if jwt_token:
            headers["Authorization"] = f"JWT {jwt_token}"
            headers["Content-Type"] = "application/json"

        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(
            _api("/api/test/validate-token"),
            json=body,
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        new_tokens = resp.json()
        print(f"Token validation successful: {new_tokens}")

        new_jwt_token = new_tokens.get("data", {}).get("new_jwt_token")
        new_refresh_token = new_tokens.get("data", {}).get("new_refresh_token")
        print(f"New JWT Token: {new_jwt_token}, New Refresh Token: {new_refresh_token}")

        # get task list data for the requested page
        body = {"page": next_page, "page_size": 1, "view_type": "available"}
        headers = {}
        if new_jwt_token:
            headers["Authorization"] = f"JWT {new_jwt_token}"
            headers["Content-Type"] = "application/json"

        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(
            _api("/api/test/init-task-list"),
            json=body,
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        ini_task_list = resp.json()
        tasks = ini_task_list.get("data", [])
        pagination_info = {"current_page": next_page}
        print(f"Task list page {next_page} retrieval successful: {tasks}")

    except requests.RequestException:
        tasks = []
        pagination_info = {"current_page": next_page}
        flash("Could not connect to backend API.", "danger")
    return render_template(
        "task_dashboard.html", tasks=tasks, pagination=pagination_info
    )


@app.route("/tasks")
def task_dashboard():
    """Render the task dashboard with nested company and URL info."""
    # Sample data mirroring TaskInfo / CompanyInfo / URLInfo schemas
    tasks = [
        {
            "id": 1,
            "task_name": "Q1 Annual Report Collection",
            "status": "In Progress",
            "priority": "High",
            "deadline": "2026-04-30",
            "total_companies": 3,
            "completed_companies": 1,
            "task_type": "Financial Report",
            "progress": 0.33,
            "task_description": "Collect Q1 annual reports for all assigned companies.",
            "companyInfos": [
                {
                    "task_id": 1,
                    "name": "Acme Corp",
                    "entity_name": "Acme Corporation Ltd.",
                    "orbit_entity_id": "ORB-001",
                    "status": "Completed",
                    "current_step": "Review",
                    "completed_at": "2026-04-01",
                    "notes": "All documents received.",
                    "shared_notes": "Reviewed by team lead.",
                    "review_rejection_reason": "",
                    "missing_reports": [],
                    "urlInfos": [
                        {
                            "id": 1,
                            "url": "https://acme.com/annual-report-2025.pdf",
                            "type": "Annual Report",
                            "comment": "Official filing",
                        },
                        {
                            "id": 2,
                            "url": "https://acme.com/auditor-statement.pdf",
                            "type": "Auditor Statement",
                            "comment": None,
                        },
                    ],
                },
                {
                    "task_id": 1,
                    "name": "Globex Industries",
                    "entity_name": "Globex Industries Inc.",
                    "orbit_entity_id": "ORB-002",
                    "status": "Pending",
                    "current_step": "Data Entry",
                    "completed_at": "",
                    "notes": "Waiting for CFO approval.",
                    "shared_notes": "",
                    "review_rejection_reason": "Missing balance sheet.",
                    "missing_reports": ["Balance Sheet", "Cash Flow Statement"],
                    "urlInfos": [
                        {
                            "id": 3,
                            "url": "https://globex.com/reports/2025",
                            "type": "Annual Report",
                            "comment": "Partial upload",
                        },
                    ],
                },
                {
                    "task_id": 1,
                    "name": "Initech Solutions",
                    "entity_name": "Initech Solutions Pte. Ltd.",
                    "orbit_entity_id": "ORB-003",
                    "status": "Pending",
                    "current_step": "Collection",
                    "completed_at": "",
                    "notes": "",
                    "shared_notes": "",
                    "review_rejection_reason": "",
                    "missing_reports": [],
                    "urlInfos": [],
                },
            ],
        },
        {
            "id": 2,
            "task_name": "ESG Disclosure Review",
            "status": "Active",
            "priority": "Medium",
            "deadline": "2026-05-15",
            "total_companies": 2,
            "completed_companies": 2,
            "task_type": "ESG",
            "progress": 1.0,
            "task_description": "Review and archive ESG disclosure documents.",
            "companyInfos": [
                {
                    "task_id": 2,
                    "name": "Umbrella Corp",
                    "entity_name": "Umbrella Corporation",
                    "orbit_entity_id": "ORB-010",
                    "status": "Completed",
                    "current_step": "Archived",
                    "completed_at": "2026-03-28",
                    "notes": "ESG report verified.",
                    "shared_notes": "Carbon neutral certification attached.",
                    "review_rejection_reason": "",
                    "missing_reports": [],
                    "urlInfos": [
                        {
                            "id": 10,
                            "url": "https://umbrella.com/esg-2025.pdf",
                            "type": "ESG Report",
                            "comment": "Certified",
                        },
                    ],
                },
                {
                    "task_id": 2,
                    "name": "Stark Industries",
                    "entity_name": "Stark Industries LLC",
                    "orbit_entity_id": "ORB-011",
                    "status": "Completed",
                    "current_step": "Archived",
                    "completed_at": "2026-03-30",
                    "notes": "All ESG metrics collected.",
                    "shared_notes": "",
                    "review_rejection_reason": "",
                    "missing_reports": [],
                    "urlInfos": [
                        {
                            "id": 11,
                            "url": "https://stark.com/sustainability-report.pdf",
                            "type": "ESG Report",
                            "comment": None,
                        },
                        {
                            "id": 12,
                            "url": "https://stark.com/carbon-offset-cert.pdf",
                            "type": "Certificate",
                            "comment": "Third-party verified",
                        },
                    ],
                },
            ],
        },
    ]
    return render_template("task_dashboard.html", tasks=tasks)


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        payload = {
            "name": request.form.get("name", "").strip(),
            "source": request.form.get("source", "").strip(),
            "value": request.form.get("value", "").strip() or None,
        }
        try:
            resp = requests.post(_api("/api/data/"), json=payload, timeout=5)
            resp.raise_for_status()
            flash("Item created successfully.", "success")
        except requests.RequestException as e:
            flash(f"Failed to create item: {e}", "danger")
        return redirect(url_for("index"))
    return render_template("create.html")


@app.route("/test", methods=["GET", "POST"])
def test():
    return render_template("test.html")


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id: int):
    try:
        resp = requests.delete(_api(f"/api/data/{item_id}"), timeout=5)
        resp.raise_for_status()
        flash("Item deleted.", "success")
    except requests.RequestException as e:
        flash(f"Failed to delete item: {e}", "danger")
    return redirect(url_for("index"))


# api token retrieval testing
@app.route("/api/test/token", methods=["POST"])
def token_auto_test():
    try:
        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(_api("/api/test/token"), timeout=60)
        # Relay the backend response as-is (including error details from FastAPI)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Cannot connect to backend at http://localhost:8000. Is uvicorn running?",
                }
            ),
            502,
        )
    except requests.exceptions.Timeout:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Backend request timed out (>60 s). Chrome may still be starting up — please try again.",
                }
            ),
            504,
        )
    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500


# api token validation testing
@app.route("/api/test/validate-token", methods=["POST"])
def token_validate_test():
    try:
        auth_header = request.headers.get("Authorization", "")
        body = request.get_json(silent=True) or {}
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(
            _api("/api/test/validate-token"), json=body, headers=headers, timeout=60
        )
        # Relay the backend response as-is (including error details from FastAPI)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Cannot connect to backend at http://localhost:8000. Is uvicorn running?",
                }
            ),
            502,
        )
    except requests.exceptions.Timeout:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Backend request timed out (>60 s). Chrome may still be starting up — please try again.",
                }
            ),
            504,
        )
    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500


# api task list testing
@app.route("/api/test/init-task-list", methods=["POST"])
def api_task_list_test():
    try:
        auth_header = request.headers.get("Authorization", "")
        body = request.get_json(silent=True) or {}
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(
            _api("/api/test/init-task-list"),
            json=body,
            headers=headers,
            timeout=60,
        )
        print(f"Task list and details API response: {resp.status_code} {resp.text}")
        # Relay the backend response as-is (including error details from FastAPI)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Cannot connect to backend at http://localhost:8000. Is uvicorn running?",
                }
            ),
            502,
        )
    except requests.exceptions.Timeout:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Backend request timed out (>60 s). Chrome may still be starting up — please try again.",
                }
            ),
            504,
        )
    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500


# api assign task testing
@app.route("/api/test/assign-task", methods=["POST"])
def api_assign_task_test():
    try:
        auth_header = request.headers.get("Authorization", "")
        body = request.get_json(silent=True) or {}
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(
            _api("/api/test/assign-task"),
            json=body,
            headers=headers,
            timeout=60,
        )
        # Relay the backend response as-is (including error details from FastAPI)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Cannot connect to backend at http://localhost:8000. Is uvicorn running?",
                }
            ),
            502,
        )
    except requests.exceptions.Timeout:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Backend request timed out (>60 s). Chrome may still be starting up — please try again.",
                }
            ),
            504,
        )
    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500


# api abandon task testing
@app.route("/api/test/abandon-task", methods=["POST"])
def api_abandon_task_test():
    try:
        auth_header = request.headers.get("Authorization", "")
        body = request.get_json(silent=True) or {}
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(
            _api("/api/test/abandon-task"),
            json=body,
            headers=headers,
            timeout=60,
        )
        # Relay the backend response as-is (including error details from FastAPI)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Cannot connect to backend at http://localhost:8000. Is uvicorn running?",
                }
            ),
            502,
        )
    except requests.exceptions.Timeout:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Backend request timed out (>60 s). Chrome may still be starting up — please try again.",
                }
            ),
            504,
        )
    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/next-task", methods=["POST"])
def api_next_task():
    """Fetch the next task (paginated, page_size=1) and return enriched TaskInfo JSON.

    Request body (JSON): { "page": <int> }
    Proxies to FastAPI /api/test/init-task-list which enriches task details.
    """
    body = request.get_json(silent=True) or {}
    page = int(body.get("page", 2))
    auth_header = request.headers.get("Authorization", "")

    try:
        # Step 1: get + validate a fresh token via the existing proxy
        token_resp = requests.post(_api("/api/test/token"), timeout=60)
        token_resp.raise_for_status()
        tokens = token_resp.json()
        jwt_token = tokens.get("jwt_token_value", "")
        refresh_token = tokens.get("refresh_token_value", "")

        # Step 2: validate / refresh the token
        val_headers = {"Content-Type": "application/json"}
        if jwt_token:
            val_headers["Authorization"] = f"JWT {jwt_token}"
        val_resp = requests.post(
            _api("/api/test/validate-token"),
            json={"refreshToken": refresh_token},
            headers=val_headers,
            timeout=60,
        )
        val_resp.raise_for_status()
        new_tokens = val_resp.json()
        new_jwt = new_tokens.get("data", {}).get("new_jwt_token") or jwt_token

        # Step 3: fetch the requested page of tasks (1 per page)
        task_headers = {
            "Authorization": f"JWT {new_jwt}",
            "Content-Type": "application/json",
        }
        task_resp = requests.post(
            _api("/api/test/init-task-list"),
            json={"page": page, "page_size": 1, "view_type": "available"},
            headers=task_headers,
            timeout=120,
        )
        task_resp.raise_for_status()
        result = task_resp.json()
        return jsonify({"success": True, "data": result.get("data", [])}), 200

    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "error": "Cannot connect to backend."}), 502
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Backend request timed out."}), 504
    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test/update", methods=["POST"])
def api_update_test():
    try:
        resp = requests.post(_api("/api/test/update"), timeout=10)
        # Relay the backend response as-is (including error details from FastAPI)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Cannot connect to backend at http://localhost:8000. Is uvicorn running?",
                }
            ),
            502,
        )
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Backend request timed out."}), 504
    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
