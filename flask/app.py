"""GOL651 - Flask example application.

Started by the "web" profile:   docker compose --profile web up -d
Open:                           http://localhost:5000

A minimal web application, for comparison with FastAPI: Flask returns HTML
pages (or JSON) from Python functions called "views". Debug mode reloads the
application when this file is saved.
"""

from __future__ import annotations

from datetime import datetime

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

PAGE = """<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>GOL651 - Flask</title></head>
<body style="font-family: sans-serif; max-width: 40rem; margin: 2rem auto;">
  <h1>GOL651 – Flask</h1>
  <p>{{ message }}</p>
  <form action="/hello">
    <label>Votre nom / Your name: <input name="name" value="{{ name }}"></label>
    <button type="submit">OK</button>
  </form>
  <p><a href="/api/time">/api/time</a> (JSON)</p>
</body>
</html>"""


@app.get("/")
def index() -> str:
    return render_template_string(PAGE, message="Bienvenue / Welcome", name="")


@app.get("/hello")
def hello() -> str:
    name = request.args.get("name", "").strip() or "GOL651"
    # Jinja escapes {{ name }} automatically: user input cannot inject HTML.
    return render_template_string(PAGE, message=f"Bonjour {name} !", name=name)


@app.get("/api/time")
def api_time():
    return jsonify(service="GOL651 Flask", server_time=datetime.now().isoformat(timespec="seconds"))
