from __future__ import annotations
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# File to store reminders
REMINDERS_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")

def load_reminders() -> list[dict]:
    """Load reminders from file"""
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def save_reminders(items: list[dict]) -> None:
    """Save reminders to file"""
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

@app.post("/api/assistant")
def assistant():
    """Handle assistant messages (reminders + time)"""
    try:
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()

        if not message:
            return jsonify({"error": "Missing 'message'"}), 400

        lower = message.lower()

        # Add reminder
        if lower.startswith("add reminder"):
            if ":" in message:
                content = message.split(":", 1)[1].strip()
            else:
                content = message[len("add reminder"):].strip(" -:")

            if not content:
                return jsonify({
                    "reply": "Please provide the reminder text, e.g., 'Add reminder: Buy milk at 5pm'."
                })

            reminders = load_reminders()
            item = {
                "id": f"r_{int(datetime.now().timestamp()*1000)}",
                "text": content,
                "created_at": datetime.now().isoformat(timespec="seconds")
            }
            reminders.append(item)
            save_reminders(reminders)

            return jsonify({
                "reply": f"Added reminder: “{content}”. You now have {len(reminders)} reminder(s)."
            })

        # Show reminders
        if lower.startswith("show reminders") or lower == "reminders":
            reminders = load_reminders()
            if not reminders:
                return jsonify({"reply": "You have no reminders yet."})
            lines = [f"{idx+1}. {r.get('text')}" for idx, r in enumerate(reminders)]
            return jsonify({"reply": "Here are your reminders:\n" + "\n".join(lines)})

        # Tell the time
        if "what time is it" in lower or lower == "time":
            now = datetime.now().astimezone()
            reply = now.strftime("It's %A, %B %d, %Y at %I:%M %p %Z.")
            return jsonify({"reply": reply})

        # Default response
        help_hint = "Try: “What time is it?”, “Show reminders”, or “Add reminder: …”."
        return jsonify({"reply": f"You said: “{message}”. {help_hint}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve HTML files
@app.get("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.get("/index.html")
def serve_index_alias():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
