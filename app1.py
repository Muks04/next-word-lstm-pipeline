import os
import streamlit as st
import pandas as pd
import requests

# Set API_URL env var to your API Gateway URL when deployed
# Falls back to local model.py for local dev
API_URL = os.getenv("API_URL", "")

# Local fallback imports (used when API_URL is not set)
if not API_URL:
    from model import load_artifacts, predict_top_n, predict_n_words

st.set_page_config(page_title="Next Word Prediction", page_icon="📖", layout="centered")


@st.cache_resource
def get_local_artifacts():
    return load_artifacts()


def get_predictions(text: str, top_n: int):
    """Call Lambda API or fall back to local model."""
    if API_URL:
        resp = requests.post(
            API_URL,
            json={"text": text, "top_n": top_n},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        words = [p["word"] for p in data["predictions"]]
        probs = [p["probability"] for p in data["predictions"]]
        return words, probs
    else:
        model, tokenizer = get_local_artifacts()
        max_seq = model.input_shape[1] + 1
        return predict_top_n(model, tokenizer, text, max_seq, top_n)


def get_extended(text: str, n: int, top_n: int):
    for _ in range(n):
        words, _ = get_predictions(text, top_n=1)
        text += " " + words[0]
    return text


# UI
st.title("📖 Next Word Prediction — LSTM")
st.caption("Trained on Shakespeare's Hamlet")

if API_URL:
    st.success(f"Running on Lambda API")
else:
    st.info("Running locally")

input_text = st.text_input("Enter a sequence of words", "To be or not to be")

col1, col2 = st.columns(2)
top_n   = col1.slider("Top N candidates", min_value=3, max_value=20, value=10)
n_words = col2.slider("Predict N next words", min_value=1, max_value=10, value=3)

if st.button("Predict", type="primary"):
    if not input_text.strip():
        st.warning("Please enter some text first.")
    else:
        with st.spinner("Predicting..."):
            top_words, top_probs = get_predictions(input_text, top_n)

        st.subheader(f"Next word: `{top_words[0]}`  —  confidence: `{top_probs[0]:.2%}`")

        df = pd.DataFrame({"Probability": top_probs}, index=top_words)
        st.bar_chart(df)

        st.subheader("Extended prediction")
        extended = get_extended(input_text, n_words, top_n)
        st.info(extended)
