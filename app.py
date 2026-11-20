import os
import socket
import time

import pymysql
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "mysql-container"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "app_user"),
    "password": os.environ.get("MYSQL_PASSWORD", "app_password"),
    "database": os.environ.get("MYSQL_DB", "flask_messages"),
    "connect_timeout": 5,
    "cursorclass": pymysql.cursors.DictCursor,
}

_db_ready = False


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def init_db():
    """Create the messages table. Safe to call more than once."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
    finally:
        conn.close()


def ensure_db():
    """Initialize lazily and retry briefly while MySQL is starting."""
    global _db_ready
    if _db_ready:
        return

    last_error = None
    for attempt in range(1, 16):
        try:
            init_db()
            _db_ready = True
            return
        except pymysql.MySQLError as exc:
            last_error = exc
            print(f"Waiting for MySQL (attempt {attempt}/15): {exc}", flush=True)
            time.sleep(2)

    raise RuntimeError("Could not initialize the database after retries") from last_error


@app.route("/health")
def health():
    # Application health only; this endpoint intentionally does not query MySQL.
    return jsonify({"status": "ok", "container": socket.gethostname()})


@app.route("/")
def hello():
    ensure_db()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, message, created_at FROM messages ORDER BY id DESC")
            messages = cur.fetchall()
    finally:
        conn.close()

    return render_template(
        "index.html",
        messages=messages,
        hostname=socket.gethostname(),
        db_host=DB_CONFIG["host"],
    )


@app.route("/submit", methods=["POST"])
def submit():
    new_message = request.form.get("new_message", "").strip()
    if not new_message:
        return jsonify({"error": "Please enter a message."}), 400

    ensure_db()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (message) VALUES (%s)",
                (new_message,),
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": new_message})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
