# Ocollector Chrome Extension — Project Summary

> Version: **1.12.0** | Manifest Version: **3** | Framework: **Vue 3 + Element Plus** | Build Tool: **Vite (WXT)**

---

## 1. Overview

**Ocollector** (Orbit 报告收集器) is an internal Chrome DevTools extension built by **OrbitFin** to help analysts collect, organize, upload, and manage financial reports (PDFs, earnings transcripts, slides, etc.) from web pages.

It runs inside Chrome DevTools as a sidebar panel and communicates with:
- A **backend API** hosted at `https://101-next.orbitfin.ai/prod` (production) or `https://101-next-staging.orbitfin.ai/prod` (staging)
- The **active browser tab** (content script injection, element selection, screenshot capture, HTTP header interception)
- **Feishu (Lark) OAuth** for user authentication

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Chrome Browser                     │
│                                                      │
│  ┌─────────────────┐     ┌────────────────────────┐  │
│  │  DevTools Panel  │     │     Active Tab          │  │
│  │  (Vue 3 UI)      │◄───►│  content-scripts/       │  │
│  │  devtools-panel  │     │  content.js             │  │
│  │  .html           │     │  (element selection,    │  │
│  └────────┬─────────┘     │   page info)            │  │
│           │               └────────────────────────┘  │
│           │ webext-bridge                              │
│  ┌────────▼─────────┐                                 │
│  │  Background SW    │  webRequest listener            │
│  │  (background.js)  │  tab/storage management         │
│  │  RPC handlers     │                                 │
│  └────────┬─────────┘                                 │
│           │ axios (JWT auth)                          │
└───────────┼──────────────────────────────────────────┘
            │ HTTPS
   ┌────────▼────────────────────┐
   │   OrbitFin Backend API      │
   │   101-next.orbitfin.ai/prod │
   └─────────────────────────────┘
```

### Key Files

| File | Role |
|------|------|
| `manifest.json` | Extension manifest (MV3), declares permissions and entry points |
| `background.js` | Service worker: routing, RPC handlers, OAuth, webRequest listener, token refresh |
| `devtools.html` | DevTools page entry — creates the DevTools panel |
| `devtools-panel.html` | The actual panel UI shell (Vue app mounts on `#app`) |
| `chunks/devtools-C3uuuVDk.js` | DevTools bootstrap — registers the panel via `chrome.devtools.panels.create` |
| `chunks/devtools-panel-DpxqPXWC.js` | Main Vue 3 SPA bundle: all UI components, stores, API functions |
| `chunks/browser-BnURzfs5.js` | Shared browser-polyfill (webext-polyfill) |
| `content-scripts/content.js` | Injected into every page: element selection overlay, page info relay |

---

## 3. Permissions

| Permission | Purpose |
|-----------|---------|
| `webRequest` | Intercept outgoing request headers from the active tab |
| `activeTab` | Access the current tab's URL, title, and send messages |
| `storage` | Persist auth tokens, settings, report type config, and per-tab company data |
| `tabs` | Query, create, update, reload tabs; capture visible tab screenshots |
| `identity` | Launch Feishu OAuth web auth flow |
| `clipboardWrite` | Copy data to clipboard |
| `<all_urls>` / `host_permissions` | Intercept requests on all URLs; inject content scripts everywhere |

---

## 4. Messaging Architecture (webext-bridge)

The extension uses **webext-bridge** (a typed cross-context messaging library) for communication between DevTools panel, background service worker, and content scripts.

### RPC Channels (background → panel)

| Channel | Direction | Purpose |
|---------|-----------|---------|
| `auth/startFeishuLogin` | Panel → Background | Trigger Feishu OAuth login flow |
| `page/startElementSelection` | Panel → Content Script | Activate element-picker overlay on current tab |
| `page/exitElementSelection` | Panel → Content Script | Deactivate element-picker |
| `page/removeHighlightOverlay` | Panel → Content Script | Remove the blue highlight overlay |
| `page/openPageInTab` | Panel → Background | Open a URL in current or new tab |
| `page/getPageHeaders` | Panel → Background | Retrieve intercepted HTTP request headers for a tab |
| `page/refreshPageForHeaders` | Panel → Background | Reload tab and clear cached headers |
| `page/captureScreenshot` | Panel → Background | Capture a PNG screenshot of the active tab |

### Content Script Messages (chrome.runtime.sendMessage)

| Action | Direction | Payload |
|--------|-----------|---------|
| `elementSelected` | Content → Background/Panel | `elementInfo` (outerHTML), `tabId`, `pageInfo` (url, title, host) |
| `setPageInfo` | Content → Background | `pageInfo` (url, title), `tabId` |
| `startElementSelection` | Background → Content | `tabId` |
| `exitElementSelection` | Background → Content | — |
| `removeHighlightOverlay` | Background → Content | — |

---

## 5. Authentication Flow

### Feishu (Lark) OAuth 2.0

1. Panel triggers `auth/startFeishuLogin` RPC → background
2. Background reads current settings to determine API base URL
3. Constructs Feishu OAuth URL:
   ```
   https://passport.feishu.cn/suite/passport/oauth/authorize
     ?client_id=cli_a13a806141b8900b
     &redirect_uri=https://<extension_id>.chromiumapp.org/
     &response_type=code
     &state=<timestamp>
   ```
4. `chrome.identity.launchWebAuthFlow` opens the Feishu login popup
5. On success, extracts `code` from redirect URL
6. POSTs to `/user/feishu_login` with `{ auth_code: code }`
7. Stores `{ access, refresh, username, user_id, avatar }` in `chrome.storage.local` under key `plugin.auth`

### JWT Token Management

- Every API request (via the configured **axios** instance) reads `plugin.auth` from storage
- Attaches header: `Authorization: JWT <access_token>`
- Also attaches: `x-client-version: 1.12.0`
- On **401** response: automatic token refresh via `POST /login/refresh` with `{ refresh }` token
- Refreshed access token is stored back; original request retried once
- On second 401 failure: auth entry removed from storage, `AuthenticationError` thrown

---

## 6. Settings & Storage Keys

| Storage Key | Contents |
|-------------|----------|
| `plugin.auth` | `{ access, refresh, username, user_id, avatar }` |
| `plugin.settings` | `{ environment, customApiUrl, model }` |
| `report_type_configuration` | Cached report type list from server |
| `plugin.lastCheckTime` | Timestamp of last update check |
| `plugin.updateAvailable` | Whether a new extension version is available |
| `company_data_<tabId>` | Per-tab company context: `{ companyId, companyInfo }` |

### Settings Defaults

```json
{
  "environment": "production",
  "customApiUrl": "http://127.0.0.1:8000",
  "model": "gpt-5"
}
```

### Environment → Base URL Mapping

| Environment | Base URL |
|-------------|----------|
| `production` | `https://101-next.orbitfin.ai/prod` |
| `staging` | `https://101-next-staging.orbitfin.ai/prod` |
| `local-dev` | `customApiUrl` (default `http://127.0.0.1:8000`) |

---

## 7. Business Logic & Workflows

### 7.1 Company Search & Report List

The panel lets users search for a company and view their existing reports.

- User enters company name/ID → panel calls `GET /filing/ocollector/get_exist_company_report_list`
- Payload: `{ orbit_entity_id, page, pageSize, search_id?, search_title?, reported_at? }`
- The company context (`companyId`, `companyInfo`) is persisted per-tab via `company_data_<tabId>` in `chrome.storage.local`
- Source pages for the company are validated against the current tab URL before allowing uploads

### 7.2 Report Upload (Manual / From File)

Full multi-step upload flow:

1. **Duplicate check by URL**: `POST /filing/ocollector/check_report_url_duplicate`
   - Checks if a report at this URL already exists
2. **Duplicate check by MD5**: `POST /filing/ocollector/check_file_md5_duplicate`
   - Checks if the same file content was previously uploaded
3. **Upload file**: `POST /filing/ocollector/upload_report_file` *(multipart/form-data)*
   - Uploads the binary file to the backend
4. **Create report record**: `POST /filing/ocollector/create_single_report` *(multipart/form-data)*
   - Associates the uploaded file with company, report type, date, and metadata
5. **Get S3 pre-signed URL** (for direct downloads): `POST /filing/ocollector/get_s3_object_presigned_url`

### 7.3 Upload From URL (Auto Download + S3)

For reports accessible via URL, the backend handles the download:

1. **Check URL duplicate**: `POST /filing/ocollector/check_report_url_duplicate`
2. **Check report existence (v3)**: `POST /filing/ocollector/check_report_exist_v3` *(multipart/form-data)*
3. **Poll for async result**: `POST /filing/ocollector/get_check_report_exist_v3_status`
4. **Trigger download & upload to S3**: `POST /security/download_report_and_upload_to_s3`
5. **Upload earnings reports batch**: `POST /security/upload_earning_reports`

### 7.4 HTML Element-Based Report Extraction (AI Analysis)

For financial data embedded directly in web pages:

1. User clicks "Element Selection" → content script activates a mouse hover + click overlay
2. User clicks on a table or data element — `outerHTML` is captured
3. `POST /filing/ocollector/analyze_report_from_html` is called with the HTML content
   - AI (GPT model configured in settings) extracts structured financial data
4. User can review and save the extracted data

### 7.5 Screenshot Capture

- Background calls `chrome.tabs.captureVisibleTab` → returns base64 PNG
- Returns: `{ imageData, pageInfo: { url, title, tabId, host, timestamp } }`

### 7.6 Report Management

- **Update report row**: `POST /filing/ocollector/update_company_single_row_report`
- **Update timestamps**: `POST /filing/ocollector/update_company_single_row_report_updated_time`
- **Delete report file**: `POST /filing/ocollector/delete_report_file`
- **Translate report title**: `POST /filing/ocollector/translate_report_title`
- **Re-parse metadata**: `POST /filing/ocollector/reparse_report_file_metadata`

### 7.7 Task Queue Management

Background download/upload tasks are tracked server-side:

- **List my tasks**: `POST /security/task/list` with `{ page: 1, page_size: 1000, view_type: "my_tasks" }`
- **Task detail**: `GET /security/task/detail?task_id=<id>`

Task status lifecycle:

| Status | Label (Chinese) | User Can Edit | User Can Process |
|--------|----------------|---------------|-----------------|
| `INIT` | 待处理 | ✅ | ✅ |
| `DOWNLOADING` | 正在下载 | ❌ | ❌ |
| `SUCCESS` | 成功 | ❌ | ❌ |
| `FAILED` | 失败 | ✅ | ✅ |
| `BAD` | 已跳过 | ❌ | ❌ |

### 7.8 Statistics Dashboard

- `POST /filing/ocollector/get_statistics` with `{ start_date, end_date }`
- Default date range: last 7 days
- Only loads if user is authenticated (checks `plugin.auth.access`)

### 7.9 Auto Update Check

Runs on a schedule (cooldown: 900 seconds = 15 minutes):

1. `GET /filing/ocollector/get_chrome_extension_latest_version`
   - Returns the latest version string
   - Compared against bundled version `1.12.0`
2. `GET /filing/ocollector/get_report_type_latest_configuration_url`
   - Fetches URL to the latest report type configuration JSON
   - Downloaded and cached in `report_type_configuration` storage key

### 7.10 HTTP Header Interception

- `chrome.webRequest.onSendHeaders` listener captures request headers for all `main_frame` navigations
- Stored in memory: `Map<tabId, RequestHeaders[]>`
- Panel can retrieve these via `page/getPageHeaders` RPC
- Used to detect authentication tokens or session cookies for target financial sites
- Headers are cleared when a tab is closed

---

## 8. API Reference

Base URL: `https://101-next.orbitfin.ai/prod` (production)

All requests carry:
- `Authorization: JWT <access_token>`
- `x-client-version: 1.12.0`

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/user/feishu_login` | Exchange Feishu OAuth code for JWT tokens |
| `POST` | `/login/refresh` | Refresh expired access token using refresh token |

### Filing / Report Collection

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/filing/ocollector/get_exist_company_report_list` | List existing reports for a company |
| `POST` | `/filing/ocollector/check_report_url_duplicate` | Check if a report URL is already collected |
| `POST` | `/filing/ocollector/check_file_md5_duplicate` | Check if file content (by MD5) is already uploaded |
| `POST` | `/filing/ocollector/upload_report_file` | Upload a report file (multipart/form-data) |
| `POST` | `/filing/ocollector/create_single_report` | Create a report record tied to uploaded file (multipart/form-data) |
| `POST` | `/filing/ocollector/update_company_single_row_report` | Edit/update a single report row |
| `POST` | `/filing/ocollector/update_company_single_row_report_updated_time` | Update a report's timestamp |
| `POST` | `/filing/ocollector/delete_report_file` | Delete a report file |
| `POST` | `/filing/ocollector/get_s3_object_presigned_url` | Get a pre-signed S3 URL for a report file |
| `POST` | `/filing/ocollector/translate_report_title` | Translate a report title (likely Chinese ↔ English) |
| `POST` | `/filing/ocollector/reparse_report_file_metadata` | Re-extract metadata from an already-uploaded file |
| `POST` | `/filing/ocollector/analyze_report_from_html` | AI-powered extraction of report data from raw HTML |
| `POST` | `/filing/ocollector/check_report_exist_v3` | Check if a report already exists (v3, async start) (multipart/form-data) |
| `POST` | `/filing/ocollector/get_check_report_exist_v3_status` | Poll for result of check_report_exist_v3 |
| `GET`  | `/filing/ocollector/get_report_type_latest_configuration_url` | Get CDN URL for report type config JSON |
| `GET`  | `/filing/ocollector/get_chrome_extension_latest_version` | Get the latest extension version string |
| `POST` | `/filing/ocollector/get_statistics` | Get collection statistics for a date range |

### Security / Tasks

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/security/task/list` | List background download tasks (paginated, my_tasks view) |
| `GET`  | `/security/task/detail?task_id=<id>` | Get detail of a specific background task |
| `POST` | `/security/download_report_and_upload_to_s3` | Trigger backend to download a report URL and upload to S3 |
| `POST` | `/security/upload_earning_reports` | Batch upload earnings reports |

---

## 9. Content Script Behavior

File: `content-scripts/content.js`

Injected into every web page (`<all_urls>`). Does not run any code proactively—only activates in response to messages from background.

### Element Selection Mode

When activated:
1. Creates an absolutely-positioned `div` overlay with blue border (`rgba(64, 158, 255, 0.2)`)
2. Tracks `mousemove` to highlight hovered DOM elements
3. On `click`: captures `element.outerHTML`, sends it back via `chrome.runtime.sendMessage`
4. Sends `{ action: "elementSelected", elementInfo, tabId, pageInfo }` and `{ action: "setPageInfo", pageInfo, tabId }`
5. Click is `preventDefault` + `stopPropagation` to prevent navigation

### Lifecycle Management

Uses WXT (`ContentScriptContext`) for:
- Detecting when a newer version of the content script has started (self-termination)
- URL change detection (via `setInterval` polling `window.location.href`)
- Signal-based abort for all registered listeners and timers

---

## 10. Report Types

Two special report type IDs are hardcoded for the "quick upload" earnings flow:

| ID | Type |
|----|------|
| `10122` | Transcript |
| `10311` | Slide |

These map to keys `transcript` and `slide` used in the earnings report upload API.

---

## 11. Technology Stack

| Layer | Technology |
|-------|-----------|
| Extension framework | WXT (Web Extension Tools) |
| UI framework | Vue 3 (Composition API) |
| UI library | Element Plus |
| HTTP client | Axios 1.13.2 (with interceptors for auth + retry) |
| Messaging | webext-bridge (typed cross-context messaging) |
| Browser polyfill | webextension-polyfill |
| Date handling | Day.js |
| Build output | Vite (ESM chunks) |
| Auth | Feishu OAuth 2.0 + JWT (access + refresh tokens) |
| File storage | AWS S3 (via pre-signed URLs) |

---

## 12. Complete API Details Table

### Common Request Headers

All authenticated endpoints carry these headers (injected automatically by the axios interceptor):

| Header | Value | Notes |
|--------|-------|-------|
| `Authorization` | `JWT <access_token>` | Omitted only on `/user/feishu_login` and `/login/refresh` |
| `x-client-version` | `1.12.0` | Extension version string |
| `Content-Type` | `application/json` | Default for JSON body requests |
| `Content-Type` | `multipart/form-data` | Form-data file upload requests (overrides default) |

### Standard Response Envelope

```json
{
  "code": 20000,
  "data": { ... },
  "message": "success"
}
```

Error codes: `401` (unauthenticated), `403` (forbidden), `20002` (URL duplicate), `20003` (already exists in system).

---

### API Table

| # | Method | Path | Request Headers | Request Body / Params | Response | Usage |
|---|--------|------|-----------------|-----------------------|----------|-------|
| 1 | `POST` | `https://101-next.orbitfin.ai/prod/user/feishu_login` | `Content-Type: application/json` | `{ "auth_code": "<oauth_code>" }` | `{ "code": 200, "data": { "access": "", "refresh": "", "username": "", "user_id": "", "avatar": "" } }` | Exchange Feishu OAuth authorization code for JWT access + refresh tokens. Called after `chrome.identity.launchWebAuthFlow` succeeds. Tokens are stored in `chrome.storage.local` under `plugin.auth`. |
| 2 | `POST` | `https://101-next.orbitfin.ai/prod/login/refresh` | `Content-Type: application/json` | `{ "refresh": "<refresh_token>" }` | `{ "access": "<new_access_token>" }` or `{ "data": { "access": "" } }` | Silently refresh an expired access token. Triggered automatically by the axios response interceptor on any `401`. New token is stored back to `plugin.auth.access` and the original request is retried once. |
| 3 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/get_exist_company_report_list` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "orbit_entity_id": <int>, "page": <int>, "pageSize": <int>, "search_id"?: "<str>", "search_title"?: "<str>", "search_reported_at"?: "<str>" }` | `{ "code": 20000, "data": [ <report_row>, ... ], "count": <total_int> }` | Load the paginated list of existing reports for a selected company. Supports filter by report ID, title substring, or date string. Results populate the main report table in the panel. |
| 4 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/check_report_url_duplicate` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "orbit_entity_id": <int>, "report_url": "<url>" }` | `{ "code": 20000, "data": { "duplicate": <bool>, "message": "", "existing_report_id": <int\|null>, "existing_report_title": "", "existing_add_by": "", "url_duplicate_info": { ... } } }` | Step 1 of URL upload flow. Checks whether a report at the given URL was already collected. If `duplicate: true`, warns the user before proceeding. |
| 5 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/check_file_md5_duplicate` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "orbit_entity_id": <int>, "file_md5": "<md5_hex>" }` | `{ "code": 20000, "data": { "duplicate": <bool>, "existing_report_id": <int\|null>, "existing_report_title": "", "existing_add_by_username": "", "existing_created_at": "", "message": "" } }` | Step 2 of file upload flow. Client computes MD5 of the selected file and checks for content-level duplicates before uploading. If `duplicate: true`, shows a warning dialog and aborts the upload. |
| 6 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/upload_report_file` | `Authorization: JWT ...`, `x-client-version: 1.12.0`, `Content-Type: multipart/form-data` | FormData: `report_id=<int>`, `file=<binary>`, `task_id?=<int>`, `task_key?=<str>` | `{ "code": 20000, "data": { "s3_path": "<s3_key>" } }` | Upload a report file binary to the backend (which stores it in S3). Returns the S3 object path. Called after MD5 duplicate check passes. Upload progress is tracked via axios `onUploadProgress`. |
| 7 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/create_single_report` | `Authorization: JWT ...`, `x-client-version: 1.12.0`, `Content-Type: multipart/form-data` | FormData: `orbit_entity_id=<int>`, `report_title=<str>`, `report_url=<str>`, `reported_at=<str>`, `report_type_id=<int>`, `s3_path?=<str>`, `task_id?=<int>`, `task_key?=<str>`, plus any extra metadata fields | `{ "code": 20000, "data": { "report_id"/<"id">: <int> } }` | Create a new report record in the database, associating the uploaded file with a company, type, date, and other metadata. This is the final step of the manual upload workflow. |
| 8 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/update_company_single_row_report` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "report_id": <int>, "reported_at": "<date_str>", "report_title": "<str>" }` | `{ "code": 20000, "message": "success" }` | Inline-edit a report's date and/or title from the panel table. Triggered when the user saves an edit in the report list row. On success also resets the report status to "pending". |
| 9 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/update_company_single_row_report_updated_time` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "report_id": <int> }` | `{ "code": 20000, "message": "success" }` | Set a report's `updated_at` timestamp to the current server time. Triggered via a "mark as updated now" action on a report row. |
| 10 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/get_s3_object_presigned_url` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "s3_path": "<s3_key>" }` | `{ "code": 20000, "data": { "presigned_url": "<signed_https_url>" } }` | Generate a temporary signed download URL for a report file stored in S3. Used when the user clicks to preview or open a report file from the panel. The URL expires after a short period. |
| 11 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/delete_report_file` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "report_id": <int> }` | `{ "code": 20000, "message": "success" }` | Delete the file attachment of a report (removes from S3 and clears `s3_path`, `file_md5`, `file_meta` on the record). The report record itself is retained but its download status is reset to `INIT`. |
| 12 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/translate_report_title` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "original_title": "<str>", "source_language": "auto", "target_language": "English" }` | `{ "code": 20000, "data": { "translated_title": "<str>" } }` | AI-translate a report title (typically Chinese → English). Triggered by the "translate" button in the report upload/edit dialog. The result is filled into the English title field. |
| 13 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/reparse_report_file_metadata` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "report_id": <int> }` | `{ "code": 20000, "data": { "file_meta": { ... }, "file_pages": <int> } }` | Re-extract PDF metadata (page count, properties) from an already-uploaded file. Used when a file's metadata was not parsed correctly at upload time. Only available if the report has a valid `s3_path`. |
| 14 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/analyze_report_from_html` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ <html_content_fields>, <page_metadata> }` (JSON body with HTML string and context) | `{ "code": 20000, "data": { <structured_financial_data> } }` | Submit raw HTML of a page element (captured by the content script element picker) to the backend AI for structured financial data extraction. The AI model (configured via `plugin.settings.model`) parses the HTML and returns structured report fields. |
| 15 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/check_report_exist_v3` | `Authorization: JWT ...`, `x-client-version: 1.12.0`, `Content-Type: multipart/form-data` | FormData with report metadata array + optional page screenshot (`screenshot_data`, `screenshot_timestamp`) | `{ "code": 20000, "data": [ { "client_index": <int>, "database_id": <int\|null>, "is_url_dup": <bool>, "check_result": { ... } }, ... ] }` | Async check (v3) whether a batch of reports already exist, including using screenshot context. Returns per-report results with `database_id` if found. Called as the first step of the batch URL-download workflow. |
| 16 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/get_check_report_exist_v3_status` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "orbit_entity_id": <int>, "report_ids": [ <db_id>, ... ] }` | `{ "code": 20000, "data": [ { "database_id": <int>, "status_download": "<status>", ... }, ... ] }` | Poll the server for updated download/existence-check status for a set of report database IDs. Called in a polling loop during the batch URL-download workflow to update per-row status in the panel UI. |
| 17 | `POST` | `https://101-next.orbitfin.ai/prod/security/download_report_and_upload_to_s3` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "report_url": "<url>" }` | `{ "code": 20000, "data": { "s3_path": "<s3_key>" } }` | Instruct the backend to download a report from the given public URL and upload it to S3. Returns the resulting S3 path. Called per-item during the batch download-upload loop. Backend handles all downloading; the extension just provides the URL. |
| 18 | `POST` | `https://101-next.orbitfin.ai/prod/security/upload_earning_reports` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "entity_id": <int>, "task_id": <int>, "report_title": "<str>", "report_url": "<url>", "reported_at": "<date_str>", "type_id_list": ["<id>", ...], "report_type": "transcript"\|"slide", "s3_path": "<s3_key>", "data_source": "official_website", "is_accurate_date": "true"\|"false" }` | `{ "code": 20000, "data": { "report_id"\|"id": <int> } }` | Register a downloaded earnings report (transcript or slide) into the database after it has been successfully uploaded to S3. Called immediately after `/security/download_report_and_upload_to_s3` succeeds. |
| 19 | `POST` | `https://101-next.orbitfin.ai/prod/security/task/list` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "page": 1, "page_size": 1000, "view_type": "my_tasks" }` | `{ "code": 20000, "data": [ <task>, ... ] }` | Retrieve the current user's background task list (download jobs). Displayed in the Tasks tab of the panel. Default: page 1, up to 1000 tasks, filtered to "my tasks". |
| 20 | `GET` | `https://101-next.orbitfin.ai/prod/security/task/detail?task_id=<id>` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | Query param: `task_id=<int>` | `{ "code": 20000, "data": { "companies": [ { "orbit_entity_id": <int>, "entity_name": "", "logo_path": "", "website": "", "website_pages": [...] }, ... ] } }` | Fetch detail for a specific background task, including the list of companies associated with the task. Used to populate the company selector when working within a specific task context. |
| 21 | `GET` | `https://101-next.orbitfin.ai/prod/filing/ocollector/get_report_type_latest_configuration_url` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | _(none)_ | `{ "code": 20000, "data": "<cdn_url_to_json>" }` | Returns the CDN URL of the latest report type configuration JSON. The extension fetches that URL and caches the result in `chrome.storage.local` under key `report_type_configuration`. Checked every 15 minutes. |
| 22 | `GET` | `https://101-next.orbitfin.ai/prod/filing/ocollector/get_chrome_extension_latest_version` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | _(none)_ | `{ "code": 20000, "data": "<version_string>" }` | Returns the latest published extension version (e.g. `"1.13.0"`). Compared to the bundled version `1.12.0`; if newer, the panel UI shows an update notification. Checked every 15 minutes (cooldown stored in `plugin.lastCheckTime`). |
| 23 | `POST` | `https://101-next.orbitfin.ai/prod/filing/ocollector/get_statistics` | `Authorization: JWT ...`, `x-client-version: 1.12.0` | `{ "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }` | `{ "code": 20000, "data": { "statistics": [ <stat_row>, ... ] } }` | Fetch the user's report collection statistics for a given date range. Default range is the last 7 days. Displayed in the Statistics tab. Only called when the user is authenticated (`plugin.auth.access` is present). |
