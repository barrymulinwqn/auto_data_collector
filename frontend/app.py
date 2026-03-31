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
        resp = requests.get(_api("/api/data/"), timeout=5)
        resp.raise_for_status()
        items = resp.json()
    except requests.RequestException:
        items = []
        flash("Could not connect to backend API.", "danger")
    # return render_template("index.html", items=items)
    # Sample data with a 'category' attribute for grouping
    data = [
        {"id": 1, "name": "Laptop", "category": "Electronics", "price": 1200},
        {"id": 2, "name": "Smartphone", "category": "Electronics", "price": 800},
        {"id": 3, "name": "Chair", "category": "Furniture", "price": 150},
        {"id": 4, "name": "Table", "category": "Furniture", "price": 300},
    ]
    return render_template("OCollector.html", items=data)


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


# api task list testing
@app.route("/api/test/task-list", methods=["POST"])
def api_task_list_test():
    try:
        auth_header = request.headers.get("Authorization", "")
        body = request.get_json(silent=True) or {}
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        # Generous timeout: Chrome may need to be launched (up to ~30 s cold start)
        resp = requests.post(
            _api("/api/test/task-list"),
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
