import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash

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
    return render_template("index.html", items=items)


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


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id: int):
    try:
        resp = requests.delete(_api(f"/api/data/{item_id}"), timeout=5)
        resp.raise_for_status()
        flash("Item deleted.", "success")
    except requests.RequestException as e:
        flash(f"Failed to delete item: {e}", "danger")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
