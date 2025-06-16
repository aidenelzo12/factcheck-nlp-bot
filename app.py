from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sentence_transformers import SentenceTransformer, util
import torch

app = Flask(__name__)

# Load model
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

# Setup Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/17cdxH2bk2u57PBG7efSzZ0iDCC5V951drD7Bl-lQmrw/edit?usp=sharing"
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).sheet1

# Load data
data = sheet.get_all_records()
claims = [row['Claim'] for row in data]
claim_embeddings = model.encode(claims, convert_to_tensor=True)

@app.route("/", methods=["GET"])
def index():
    return "✅ FactCheck NLP Bot is running."

@app.route("/check", methods=["POST"])
def check():
    query = request.json.get("query", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    query_embedding = model.encode(query, convert_to_tensor=True)
    cos_scores = util.pytorch_cos_sim(query_embedding, claim_embeddings)[0]
    top_result = torch.topk(cos_scores, k=1)
    score = top_result.values.item() * 100
    idx = top_result.indices.item()
    best_match = data[idx]

    if score > 40:
        return jsonify({
            "match_score": round(score, 2),
            "claim": best_match['Claim'],
            "verdict": best_match['Verdict'],
            "explanation": best_match['Explanation'],
            "source": best_match['Source']
        })
    else:
        return jsonify({"message": "দুঃখিত, আমরা এই দাবিটির সত্যতা যাচাই করতে পারিনি।", "match_score": round(score, 2)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)