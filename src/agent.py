import os
import re
import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from pydantic import BaseModel, Field

# ------------------------------------------------------------
# 1. Global State & Initialization
# ------------------------------------------------------------

retrieval_vectorizer = None
customer_matrix = None
historical_pairs_dev = None

VALID_INTENTS = [
    "ACCOUNT_LOGIN",
    "APPLE_SERVICE_ISSUE",
    "PURCHASE_BILLING",
    "DEVICE_PERFORMANCE",
    "BATTERY_CHARGING",
    "IOS_UPDATE_ISSUE",
    "HARDWARE_REPAIR",
    "NETWORK_CONNECTIVITY",
    "FEATURE_SETTINGS",
    "CONTEXT_REQUIRED",
    "UNKNOWN_ESCALATE"
]

def initialize_agent():
    """Load data and initialize TF-IDF. No ML intent model is trained here."""
    global retrieval_vectorizer, customer_matrix, historical_pairs_dev
    
    if historical_pairs_dev is not None:
        return # Already initialized
        
    base_dir = os.path.dirname(__file__)
    project_root = os.path.join(base_dir, "..")
    
    def find_file(filename):
        for root, dirs, files in os.walk(project_root):
            if filename in files:
                return os.path.join(root, filename)
        return None

    csv_path = find_file("historical_support_pairs_dev.csv")
    if not csv_path:
        # Generate the file if it doesn't exist
        development_csv = find_file("development_set.csv")
        apple_csv = find_file("apple_support.csv")
        if not development_csv or not apple_csv:
            raise FileNotFoundError("Could not find development_set.csv or apple_support.csv to build retrieval pairs.")
        
        print("Generating historical_support_pairs_dev.csv...")
        development = pd.read_csv(development_csv)
        apple = pd.read_csv(apple_csv)
        
        dev_customers = development[development["inbound"] == True].copy()
        support_replies = apple[apple["inbound"] == False].copy()
        
        dev_pairs = dev_customers.merge(
            support_replies[["tweet_id", "text", "in_response_to_tweet_id"]],
            left_on="tweet_id",
            right_on="in_response_to_tweet_id",
            how="inner",
            suffixes=("_customer", "_support")
        )
        
        historical_pairs_dev_df = dev_pairs[[
            "tweet_id_customer", "text_customer", "tweet_id_support", "text_support"
        ]].rename(columns={
            "tweet_id_customer": "customer_tweet_id",
            "text_customer": "customer_text",
            "tweet_id_support": "support_tweet_id",
            "text_support": "support_reply"
        })
        
        target_dir = os.path.dirname(development_csv)
        csv_path = os.path.join(target_dir, "historical_support_pairs_dev.csv")
        historical_pairs_dev_df.to_csv(csv_path, index=False)
        historical_pairs_dev = historical_pairs_dev_df
    else:
        historical_pairs_dev = pd.read_csv(csv_path)
    
    # Fit TF-IDF
    retrieval_vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        max_features=50000,
        stop_words="english"
    )
    customer_matrix = retrieval_vectorizer.fit_transform(
        historical_pairs_dev["customer_text"].fillna("")
    )

# ------------------------------------------------------------
# 2. Rule-Based Fallback Intent
# ------------------------------------------------------------

def rule_based_intent(text):
    text = str(text).lower()
    context_words = [
        "thanks", "thank you", "thx", "okay", "ok", "yes",
        "that worked", "works now", "done", "i tried that"
    ]
    if (len(text.strip()) < 20 or any(word in text for word in context_words) 
        and not any(issue in text for issue in ["password", "wifi", "battery", "update"])):
        return "CONTEXT_REQUIRED"
    if re.search(r"\b(apple id|icloud password|password|login|log in|sign in|signin|activation lock|account)\b", text):
        return "ACCOUNT_LOGIN"
    if re.search(r"\b(payment|paying|paid|charge|charged|billing|subscription|purchase|purchased|order|preorder|refund)\b", text):
        return "PURCHASE_BILLING"
    if re.search(r"\b(battery|battery drain|draining|charging|charger|overheat|overheating|hot)\b", text):
        return "BATTERY_CHARGING"
    if re.search(r"\b(ios update|ios 1[0-9]|ios 11|ios 12|ios 13|ios 14|ios 15|ios 16|ios 17|ios 18|updated|update|updating|downgrade)\b", text):
        return "IOS_UPDATE_ISSUE"
    if re.search(r"\b(wifi|wi-fi|internet|bluetooth|mobile data|cellular|network|signal|connection|connect|connecting)\b", text):
        return "NETWORK_CONNECTIVITY"
    if re.search(r"\b(broken|screen|display|button|home button|speaker|earphones|headphones|hardware|repair|replacement|replace|warranty|damaged|damage)\b", text):
        return "HARDWARE_REPAIR"
    if re.search(r"\b(apple music|itunes|apple pay|app store|icloud sync|syncing|apple service)\b", text):
        return "APPLE_SERVICE_ISSUE"
    if re.search(r"\b(slow|lag|lagging|freeze|freezing|frozen|crash|crashing|crashes|performance)\b", text):
        return "DEVICE_PERFORMANCE"
    if re.search(r"\b(keyboard|camera|setting|settings|notification|airplay|storage|app|apps|feature|volume|music tab|lightning|autocorrect)\b", text):
        return "FEATURE_SETTINGS"
    return "UNKNOWN_ESCALATE"

# ------------------------------------------------------------
# 3. Gemini Helpers
# ------------------------------------------------------------

def get_gemini_client():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            if "GOOGLE_API_KEY" in st.secrets:
                api_key = st.secrets["GOOGLE_API_KEY"]
        except:
            pass
            
    if api_key:
        try:
            return genai.Client(api_key=api_key)
        except Exception:
            pass
            
    try:
        # Fallback to Application Default Credentials
        return genai.Client()
    except Exception as e:
        print(f"Failed to init Gemini Client: {e}")
        return None

def predict_intent_gemini(message, client):
    prompt = f"""
Analyze the following AppleSupport customer message and classify its intent.

Message: "{message}"

Valid Intents:
{", ".join(VALID_INTENTS)}

Return a JSON object with EXACTLY these keys:
- "predicted_intent": One of the Valid Intents
- "confidence": A float between 0.0 and 1.0 representing your confidence
- "reason": A short 1-sentence reason for this classification

Return ONLY valid JSON.
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash", # Use standard flash model
            contents=prompt,
            config={"temperature": 0.1, "response_mime_type": "application/json"}
        )
        data = json.loads(response.text.strip())
        intent = data.get("predicted_intent", "UNKNOWN_ESCALATE")
        if intent not in VALID_INTENTS:
            intent = "UNKNOWN_ESCALATE"
        return intent, float(data.get("confidence", 0.5)), data.get("reason", "Inferred by Gemini.")
    except Exception as e:
        print(f"Gemini Intent Error: {e}")
        return rule_based_intent(message), 0.5, "Fallback local classifier."

# ------------------------------------------------------------
# 4. Retrieval & Escalation
# ------------------------------------------------------------

def retrieve_similar_cases(query, top_k=3):
    query_vector = retrieval_vectorizer.transform([str(query)])
    similarities = cosine_similarity(query_vector, customer_matrix)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]
    results = historical_pairs_dev.iloc[top_indices].copy()
    results["similarity"] = similarities[top_indices]
    return results[["customer_tweet_id", "customer_text", "support_tweet_id", "support_reply", "similarity"]]

def decide_escalation(predicted_intent, intent_confidence, retrieved_cases):
    always_escalate = {
        "ACCOUNT_LOGIN",
        "PURCHASE_BILLING",
        "HARDWARE_REPAIR",
        "CONTEXT_REQUIRED",
        "UNKNOWN_ESCALATE"
    }
    if predicted_intent in always_escalate:
        return "ESCALATE", f"{predicted_intent} requires human support handling."
    if retrieved_cases.empty:
        return "ESCALATE", "No relevant historical AppleSupport evidence was found."
    top_similarity = float(retrieved_cases["similarity"].max())
    if top_similarity < 0.20:
        return "ESCALATE", "Historical evidence is too weak to safely ground an automated reply."
    if intent_confidence < 0.15 and top_similarity < 0.30:
        return "ESCALATE", "Both intent confidence and historical evidence are weak."
    return "AUTO_HANDLE", "Similar historical AppleSupport cases were handled."

def format_evidence(retrieved_cases):
    if retrieved_cases.empty:
        return "No historical evidence available."
    evidence = []
    for i, row in retrieved_cases.reset_index(drop=True).iterrows():
        evidence.append(
            f"CASE {i+1} — similarity {float(row['similarity']):.3f}\n"
            f"Customer:\n{str(row['customer_text'])}\n\n"
            f"AppleSupport response:\n{str(row['support_reply'])}"
        )
    return "\n\n".join(evidence)

def sanitize_reply(reply):
    # Remove usernames (e.g. @123456, @AppleSupport)
    reply = re.sub(r'@\w+', '', reply)
    # Remove t.co URLs
    reply = re.sub(r'https?://t\.co/\S+', '', reply)
    # Remove isolated long numbers that look like tweet IDs
    reply = re.sub(r'\b\d{5,20}\b', '', reply)
    # Remove multiple spaces/newlines
    reply = re.sub(r' +', ' ', reply)
    return reply.strip()

# ------------------------------------------------------------
# 5. Agent Pipeline
# ------------------------------------------------------------

def run_agent_pipeline(message):
    message = str(message).strip()
    if not message:
        raise ValueError("Customer message is empty.")

    initialize_agent()
    client = get_gemini_client()
    gemini_active = client is not None

    if gemini_active:
        predicted_intent, intent_confidence, reason = predict_intent_gemini(message, client)
    else:
        predicted_intent, intent_confidence, reason = rule_based_intent(message), 0.5, "Fallback local classifier."

    retrieved_cases = retrieve_similar_cases(message, top_k=3)
    decision, escalation_reason = decide_escalation(predicted_intent, intent_confidence, retrieved_cases)
    evidence_text = format_evidence(retrieved_cases)

    result = {
        "predicted_intent": predicted_intent,
        "intent_confidence": round(float(intent_confidence), 4),
        "intent_reason": reason,
        "decision": decision,
        "escalation_reason": escalation_reason,
        "evidence_text": evidence_text,
        "retrieved_cases": retrieved_cases,
        "gemini_active": gemini_active,
        "draft_reply": ""
    }

    if gemini_active:
        prompt = f"""
You are the AI customer-support assistant for a prototype based on AppleSupport.
Write a NEW reply for the current customer based on the intent and historical evidence.

CUSTOMER MESSAGE: {message}
INTENT: {predicted_intent}
DECISION: {decision}

HISTORICAL EVIDENCE:
{evidence_text}

RULES:
1. Do not invent policies, refunds, or technical solutions not in the evidence.
2. If DECISION is ESCALATE, the reply MUST politely ask the customer to send a DM (Direct Message) so we can look into it.
3. If DECISION is AUTO_HANDLE, provide helpful information directly. Do NOT ask them to send a DM.
4. Do NOT include usernames (like @123456).
5. Do NOT include URLs (like t.co links).
6. Do NOT include historical tweet IDs.
7. NEVER copy a historical reply verbatim. Paraphrase and create a friendly, new response.

Return a JSON object with exactly one key:
{{
  "draft_reply": "your generated reply"
}}
"""
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config={"temperature": 0.2, "response_mime_type": "application/json"}
            )
            data = json.loads(response.text.strip())
            draft = data.get("draft_reply", "")
            result["draft_reply"] = sanitize_reply(draft)
            return result
        except Exception as e:
            print(f"Gemini generation error: {e}")

    # Fallback mode draft
    if decision == "ESCALATE":
        result["draft_reply"] = "We'd like to look into this with you. Please send us a direct message so we can gather more details."
    else:
        if not retrieved_cases.empty:
            base_reply = sanitize_reply(retrieved_cases.iloc[0]["support_reply"])
            result["draft_reply"] = f"Based on similar cases, here is some information: {base_reply} (Local Fallback Template)"
        else:
            result["draft_reply"] = "Please DM us for further assistance."

    return result
