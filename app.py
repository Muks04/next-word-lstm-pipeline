import streamlit as st
import numpy as np
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

#Load the LSTM Model
model=load_model('Best_Tuned_Next_words_LSTM.h5', compile=False)

#3 Laod the tokenizer
with open('tokenizer.pickle','rb') as handle:
    tokenizer=pickle.load(handle)

# Function to predict the next word
def predict_next_word(model, tokenizer, text, max_sequence_len):
    token_list = tokenizer.texts_to_sequences([text])[0]
    if len(token_list) >= max_sequence_len:
        token_list = token_list[-(max_sequence_len-1):]  # Ensure the sequence length matches max_sequence_len-1
    token_list = pad_sequences([token_list], maxlen=max_sequence_len-1, padding='pre')
    predicted = model.predict(token_list, verbose=0)
    predicted_word_index = np.argmax(predicted, axis=1)
    for word, index in tokenizer.word_index.items():
        if index == predicted_word_index[0]:
            return word
    return None

# streamlit app
# UI
st.title("📖 Next Word Prediction — LSTM")
st.caption("Trained on Shakespeare's Hamlet")

input_text = st.text_input("Enter a sequence of words", "To be or not to be")

col1, col2 = st.columns(2)
top_n   = col1.slider("Top N candidates", min_value=3, max_value=20, value=10)
n_words = col2.slider("Predict N next words", min_value=1, max_value=10, value=3)

if st.button("Predict", type="primary"):
    if not input_text.strip():
        st.warning("Please enter some text first.")
    else:
        top_words, top_probs = predict_top_n(model, tokenizer, input_text, max_sequence_len, top_n=top_n)

        st.subheader(f"Next word: `{top_words[0]}`  —  confidence: `{top_probs[0]:.2%}`")

        # Probability bar chart
        df = pd.DataFrame({"Probability": top_probs}, index=top_words)
        st.bar_chart(df)

        # Extended prediction
        st.subheader("Extended prediction")
        extended = predict_n_words(model, tokenizer, input_text, n_words, max_sequence_len)
        st.info(f"{extended}")

