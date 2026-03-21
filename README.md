# auto_data_collector
Auto data collector with a **FastAPI** backend and **Flask** frontend.

## Project Structure

```
auto_data_collector/
├── backend/                  # FastAPI REST API
│   ├── main.py               # App entry point & CORS config
│   ├── routers/
│   │   └── data.py           # /api/data CRUD endpoints
│   └── schemas/
│       └── data.py           # Pydantic request/response models
├── frontend/                 # Flask web UI
│   ├── app.py                # Flask app & routes
│   ├── templates/
│   │   ├── index.html        # Data listing page
│   │   └── create.html       # New item form
│   └── static/
│       ├── css/style.css
│       └── js/main.js
├── .env.example              # Environment variable template
├── requirements.txt          # All Python dependencies
└── README.md
```

## Setup

### Virtual Environment

This project uses a Python virtual environment located at `.venv/` (Python 3.13.0).

**Create the virtual environment:**
```bash
python3 -m venv .venv
```

**Activate the virtual environment:**
```bash
source .venv/bin/activate
```

**Deactivate when done:**
```bash
deactivate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

```bash
cp .env.example .env
# Edit .env as needed
```

## Running the App

**Start the FastAPI backend** (default: http://localhost:8000):
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Start the Flask frontend** (default: http://localhost:5002):
```bash
python -m frontend.app
```

Open http://localhost:5002 in your browser.

> **Note:** Ports 5000 and 5001 are reserved by macOS (AirPlay Receiver). The frontend uses port 5002 to avoid this conflict.

## API Docs

FastAPI provides interactive documentation automatically:
- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc
