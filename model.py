import ast
import difflib
from pathlib import Path
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score


# =========================
# 1. Load Intent Dataset
# =========================

intent_dataset = pd.read_csv("data/intent_dataset.csv")

X = intent_dataset["query"]
y = intent_dataset["intent"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# =========================
# 2. TF-IDF + Logistic Regression (with Joblib persistence)
# =========================

MODEL_DIR = Path(__file__).resolve().parent / "models"
TFIDF_PATH = MODEL_DIR / "tfidf.joblib"
INTENT_MODEL_PATH = MODEL_DIR / "intent_model.joblib"

if TFIDF_PATH.exists() and INTENT_MODEL_PATH.exists():

    # Load the previously trained artifacts (no retraining)

    tfidf = joblib.load(TFIDF_PATH)
    model = joblib.load(INTENT_MODEL_PATH)

else:

    tfidf = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2)
    )

    X_train_tfidf = tfidf.fit_transform(X_train)

    model = LogisticRegression(
        max_iter=1000,
        random_state=42
    )

    model.fit(X_train_tfidf, y_train)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(tfidf, TFIDF_PATH)
    joblib.dump(model, INTENT_MODEL_PATH)


# =========================
# 3. Evaluate the Model
# =========================

X_test_tfidf = tfidf.transform(X_test)

y_pred = model.predict(X_test_tfidf)

test_accuracy = accuracy_score(y_test, y_pred)
test_f1 = f1_score(y_test, y_pred, average="macro")

print(
    "Intent classifier evaluation - "
    f"test accuracy: {test_accuracy:.4f}, "
    f"macro F1-score: {test_f1:.4f}"
)


# =========================
# 4. Load Medicine Dataset
# =========================

medicine_df = pd.read_csv("data/medicine_data.csv")

medicine_names = medicine_df["medicine_name"].dropna().tolist()

# Precomputed once (instead of re-sorting on every query):
# names sorted longest-first so that longer names such as
# "Levocetirizine" are matched before shorter overlapping names.
sorted_medicine_names = sorted(
    medicine_names,
    key=lambda x: len(str(x)),
    reverse=True
)

# Lower-cased copies used for fast matching and fuzzy suggestions.
medicine_names_lower = [str(name).lower() for name in medicine_names]


# =========================
# 5. Predict Intent
# =========================

# Question phrasings that are under-represented in the training data
# (e.g. "warning about X", "precautions for X"). They act as a fallback
# hint only when the classifier predicts the generic "medicine_info"
# intent, so they can never override a more specific prediction and
# cannot reduce the measured test accuracy.
INTENT_PHRASE_HINTS = {
    "dosage": (
        "dose", "dosage", "how much", "how many", "how often",
        "how should i take", "how do i take", "how to take"
    ),
    "uses": (
        "used for", "use for", "good for", "help with",
        "cure", "treat", "benefit"
    ),
    "side_effects": (
        "side effect", "adverse effect", "adverse reaction"
    ),
    "warnings": (
        "warning", "precaution", "contraindication",
        "should avoid", "should not", "avoid taking",
        "not safe", "unsafe", "risk", "safety",
        "who should not", "interact"
    ),
    "summary": (
        "summary", "summarize", "summarise", "overview",
        "in brief", "in short", "concise"
    ),
}


def apply_phrase_hints(query, predicted_intent):
    """
    Fallback hint layer for question styles the classifier may not have
    seen. Only fires when the classifier returned the generic
    "medicine_info" intent.
    """

    if predicted_intent != "medicine_info":
        return predicted_intent

    query_lower = query.lower()

    for intent, phrases in INTENT_PHRASE_HINTS.items():

        if any(phrase in query_lower for phrase in phrases):
            return intent

    return predicted_intent


def predict_intent(query):

    query_tfidf = tfidf.transform([query])

    predicted_intent = model.predict(query_tfidf)[0]

    return apply_phrase_hints(query, predicted_intent)


# =========================
# 6. Identify Medicine
# =========================

def identify_medicine(query):

    query_lower = query.lower()

    for medicine in sorted_medicine_names:

        medicine_lower = str(medicine).lower()

        if medicine_lower in query_lower:
            return medicine

    return None


def suggest_medicines(query, limit=3):
    """
    Suggest possible medicines when the exact name is not found,
    e.g. "paracitamol" -> ["Paracetamol"]. Single words and adjacent
    word pairs are matched so that multi-word names such as
    "Folic Acid" are also covered.
    """

    tokens = query.lower().split()

    candidates = tokens + [
        " ".join(tokens[i:i + 2]) for i in range(len(tokens) - 1)
    ]

    suggestions = []

    for candidate in candidates:

        matches = difflib.get_close_matches(
            candidate,
            medicine_names_lower,
            n=limit,
            cutoff=0.75
        )

        for match in matches:

            if match not in suggestions:
                suggestions.append(match)

        if len(suggestions) >= limit:
            break

    # Map back to the original (capitalised) medicine names

    name_map = {str(name).lower(): name for name in medicine_names}

    return [name_map[match] for match in suggestions[:limit]]


# =========================
# 7. Get Medicine Information
# =========================

def format_list_field(value):
    """
    Parse a stringified list like '["Headache","Fever"]' and return it
    as readable bullet points. Falls back to the raw text if the value
    is not a valid list literal.
    """

    try:
        parsed = ast.literal_eval(value)

    except (ValueError, SyntaxError):
        parsed = None

    if isinstance(parsed, (list, tuple)):

        items = [
            str(item).strip()
            for item in parsed
            if str(item).strip()
        ]

        if items:
            return "\n".join(f"• {item}" for item in items)

    return str(value)


def get_medicine_information(medicine, intent):

    medicine_row = medicine_df[
        medicine_df["medicine_name"] == medicine
    ].iloc[0]

    if intent == "medicine_info":

        return {
            "Medicine Name": medicine,
            "Description": medicine_row["description"],
            "Uses": format_list_field(medicine_row["uses"]),
            "Side Effects": format_list_field(medicine_row["side_effects"]),
            "Disclaimer": medicine_row["disclaimer"]
        }

    elif intent == "uses":

        return {
            "Medicine Name": medicine,
            "Uses": format_list_field(medicine_row["uses"])
        }

    elif intent == "dosage":

        return {
            "Medicine Name": medicine,
            "Dosage": medicine_row["dosage"]
        }

    elif intent == "side_effects":

        return {
            "Medicine Name": medicine,
            "Side Effects": format_list_field(medicine_row["side_effects"])
        }

    elif intent == "warnings":

        return {
            "Medicine Name": medicine,
            "Warnings": medicine_row["disclaimer"]
        }

    elif intent == "summary":

        return {
            "Medicine Name": medicine,
            "Summary": medicine_row["description"]
        }


# =========================
# 8. Process User Query
# =========================

def process_query(query):

    medicine = identify_medicine(query)

    if medicine is None:

        suggestions = suggest_medicines(query)

        message = (
            "Sorry, I could not identify the medicine. "
            "Please provide a valid medicine name."
        )

        if suggestions:
            message += " Did you mean: " + ", ".join(suggestions) + "?"

        return {
            "status": "error",
            "message": message
        }

    intent = predict_intent(query)

    information = get_medicine_information(
        medicine,
        intent
    )

    return {
        "status": "success",
        "medicine": medicine,
        "intent": intent,
        "information": information
    }


# =========================
# 9. Generate Response
# =========================

def generate_response(result):

    if result["status"] == "error":
        return result["message"]

    medicine = result["medicine"]
    intent = result["intent"]
    information = result["information"]

    if intent == "medicine_info":

        response = f"""
💊 {medicine}

{information["Description"]}

Uses:
{information["Uses"]}

Side Effects:
{information["Side Effects"]}

Disclaimer:
{information["Disclaimer"]}
"""

    elif intent == "uses":

        response = f"""
🎯 Common Uses of {medicine}

{information["Uses"]}
"""

    elif intent == "dosage":

        # The dosage field already contains the complete message
        # ("...as prescribed by your doctor or physician."), so the
        # previously duplicated warning line has been removed.

        response = f"""
💊 Dosage

{information["Dosage"]}
"""

    elif intent == "side_effects":

        response = f"""
⚠️ Side Effects of {medicine}

{information["Side Effects"]}
"""

    elif intent == "warnings":

        response = f"""
⚠️ Warnings / Safety Information

{information["Warnings"]}
"""

    elif intent == "summary":

        response = f"""
📋 Summary of {medicine}

{information["Summary"]}
"""

    else:

        response = str(information)

    return response


# =========================
# 10. Test the Model
# =========================

if __name__ == "__main__":

    test_queries = [
        "What is paracetamol?",
        "What is paracetamol used for?",
        "What is the dosage of paracetamol?",
        "What are the side effects of paracetamol?",
        "Give me a summary of paracetamol",
        "Warning about amlodipine",
        "Precautions for metformin"
    ]

    for query in test_queries:

        result = process_query(query)

        print("\nUser:", query)
        print("Intent:", result.get("intent"))
        print(generate_response(result))
