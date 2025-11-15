from flask import Flask, render_template, request, jsonify
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Load the saved model and tokenizer
model_path = "saved_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()

# CSV file path
CSV_FILE = "Reviews.csv"

# Create CSV file if not exists
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=["ID", "Order ID", "Customer Name", "Phone", "DateTime", "Review", "Prediction"]).to_csv(CSV_FILE, index=False)

@app.route('/')
def home():
    return render_template('Reviews.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    text = data.get("text")
    order_id = data.get("order_id", "N/A")
    customer_name = data.get("name", "Anonymous")
    phone = data.get("phone", "")

    # Tokenize input
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Predict
    with torch.no_grad():
        outputs = model(**inputs)
        predicted_class = outputs.logits.argmax(dim=-1).item()

    if predicted_class == 1:
        prediction = "Positive"
        message = "🎉 Thank you! Enjoyed your meal. You're always welcome! 🎊"
    else:
        prediction = "Negative"
        message = "😞 We're sorry to hear that. We apologize for any inconvenience caused."

    # Read CSV
    df = pd.read_csv(CSV_FILE)

    # Generate automatic ID (like index)
    new_id = df["ID"].max() + 1 if not df.empty else 1

    # Append new row
    new_row = {
        "ID": new_id,
        "Order ID": order_id,
        "Customer Name": customer_name,
        "Phone": phone,
        "DateTime": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Review": text,
        "Prediction": prediction
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

    return jsonify({"prediction": prediction, "message": message})

if __name__ == "__main__":
    app.run(debug=True)
