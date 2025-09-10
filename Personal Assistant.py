from __future__ import annotations
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI  # OpenAI library

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# OpenAI Client with direct API key (replace with your actual key)
client = OpenAI(api_key="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")

# File to store reminders
REMINDERS_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")

def load_reminders() -> list[dict]:
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
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

@app.post("/api/assistant")
def assistant():
    try:
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()

        if not message:
            return jsonify({"error": "Missing 'message'"}), 400

        lower = message.lower()

        if lower.startswith("add reminder"):
            if ":" in message:
                content = message.split(":", 1)[1].strip()
            else:
                content = message[len("add reminder"):].strip(" -:")

            if not content:
                return jsonify({"reply": "Please provide the reminder text, e.g., 'Add reminder: Buy milk at 5pm'."})

            reminders = load_reminders()
            item = {
                "id": f"r_{int(datetime.now().timestamp()*1000)}",
                "text": content,
                "created_at": datetime.now().isoformat(timespec="seconds")
            }
            reminders.append(item)
            save_reminders(reminders)
            return jsonify({"reply": f"Added reminder: “{content}”. You now have {len(reminders)} reminder(s)."})

        if lower.startswith("show reminders") or lower == "reminders":
            reminders = load_reminders()
            if not reminders:
                return jsonify({"reply": "You have no reminders yet."})
            lines = [f"{idx+1}. {r.get('text')}" for idx, r in enumerate(reminders)]
            return jsonify({"reply": "Here are your reminders:\n" + "\n".join(lines)})

        if "what time is it" in lower or lower == "time":
            now = datetime.now().astimezone()
            reply = now.strftime("It's %A, %B %d, %Y at %I:%M %p %Z.")
            return jsonify({"reply": reply})

        help_hint = "Try: “What time is it?”, “Show reminders”, or “Add reminder: …”."
        return jsonify({"reply": f"You said: “{message}”. {help_hint}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------- AI Webpage Generator --------
@app.post("/generate_page")
def generate_page():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "create a web page")

        if not prompt:
            return jsonify({"error": "Missing 'prompt'"}), 400

        # Call OpenAI to generate HTML using chat completions
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Generate a complete HTML page based on this request: {prompt}"}
            ]
        )

        html_code = response.choices[0].message.content

        # Save HTML to file
        with open("generated.html", "w", encoding="utf-8") as f:
            f.write(html_code)

        return jsonify({"reply": "Web page generated successfully!", "url": "/generated.html"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve HTML files
@app.get("/")
def serve_index():
    return send_from_directory(".", "assistent.html")

@app.get("/index.html")
def serve_index_alias():
    return send_from_directory(".", "assistent.html")

@app.get("/generated.html")
def serve_generated():
    return send_from_directory(".", "generated.html")

if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
