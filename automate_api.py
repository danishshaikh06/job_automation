from flask import Flask, request, jsonify
from flask_cors import CORS
from danish_job_bot import run_job_automation
import os

app = Flask(__name__)

# ✅ Allow CORS only for your Lovable project URL
CORS(app, origins=["https://e767f60a-7ae5-4f5d-8491-ef84c478d50c.lovableproject.com"])

@app.route("/apply", methods=["POST"])
def apply():
    data = request.json

    required_fields = ["search_term", "resume_path", "cover_letter_path"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    results = run_job_automation(
        search_term=data["search_term"],
        resume_path=data["resume_path"],
        cover_letter_path=data["cover_letter_path"],
        max_jobs=data.get("max_jobs", 5),
        location=data.get("location", ""),
        experience_level=data.get("experience_level", ""),
        job_type=data.get("job_type", ""),
        date_posted=data.get("date_posted", "")
    )

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

