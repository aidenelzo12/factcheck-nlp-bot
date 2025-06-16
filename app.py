# app.py

from flask import Flask, request, jsonify
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from rapidfuzz import fuzz

app = Flask(__name__)

# ১. Google Sheet সেটআপ
SHEET_URL = "https://docs.google.com/spreadsheets/d/17cdxH2bk2u57PBG7efSzZ0iDCC5V951drD7Bl-lQmrw/edit?usp=sharing"
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).sheet1
sheet_data = sheet.get_all_records()  # Google Sheet থেকে নেয়া ডেটা

@app.route("/", methods=["GET"])
def index():
    return "✅ FactCheck Bot চলছে"

@app.route("/check", methods=["POST"])
def check():
    # ১. JSON সেফলি পার্স করা
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    query = payload.get("query", "").strip()
    if not query:
        return jsonify({"error": "অনুগ্রহ করে 'query' ফিল্ড পূরণ করুন"}), 400

    # ২. RapidFuzz দিয়ে ফাজি ম্যাচিং
    best_match = None
    best_score = 0
    for row in sheet_data:
        score = fuzz.token_set_ratio(query, row['Claim'])
        if score > best_score:
            best_score, best_match = score, row

    # ৩. রেসপন্স
    if best_match and best_score > 50:
        return jsonify({
            "match_score": best_score,
            "claim": best_match['Claim'],
            "verdict": best_match['Verdict'],
            "explanation": best_match['Explanation'],
            "source": best_match['Source']
        })
    else:
        return jsonify({
            "message": "দুঃখিত, ম্যাচ মেলেনি",
            "match_score": best_score
        }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
