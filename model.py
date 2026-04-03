import os
import pickle
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

MODEL_SOURCE    = os.getenv("MODEL_SOURCE", "local")
S3_BUCKET       = os.getenv("S3_BUCKET", "your-bucket-name")
MODEL_KEY       = os.getenv("MODEL_KEY", "models/next_word_lstm_model_with_early_stopping.h5")
TOKENIZER_KEY   = os.getenv("TOKENIZER_KEY", "models/tokenizer.pickle")
LOCAL_MODEL     = "next_word_lstm_model_with_early_stopping.h5"
LOCAL_TOKENIZER = "tokenizer.pickle"


class CompatibleLSTM(tf.keras.layers.LSTM):
    """Strips unsupported kwargs when loading models saved with older TF versions."""
    def __init__(self, *args, **kwargs):
        kwargs.pop("time_major", None)
        super().__init__(*args, **kwargs)


def _download_from_s3(key: str, dest: str) -> None:
    import boto3
    s3 = boto3.client("s3")
    s3.download_file(S3_BUCKET, key, dest)


def load_artifacts():
    """Load model and tokenizer from S3 or local disk based on MODEL_SOURCE env var."""
    model_path     = "/tmp/model.h5"
    tokenizer_path = "/tmp/tokenizer.pickle"

    if MODEL_SOURCE == "s3":
        _download_from_s3(MODEL_KEY, model_path)
        _download_from_s3(TOKENIZER_KEY, tokenizer_path)
    else:
        model_path     = LOCAL_MODEL
        tokenizer_path = LOCAL_TOKENIZER

    model = load_model(
        model_path,
        custom_objects={"LSTM": CompatibleLSTM},
        compile=False,
    )

    with open(tokenizer_path, "rb") as f:
        tokenizer = pickle.load(f)

    return model, tokenizer


def predict_top_n(model, tokenizer, text: str, max_sequence_len: int, top_n: int = 10):
    """Return top-N predicted next words with their probabilities."""
    token_list = tokenizer.texts_to_sequences([text])[0]
    if len(token_list) >= max_sequence_len:
        token_list = token_list[-(max_sequence_len - 1):]
    token_list = pad_sequences([token_list], maxlen=max_sequence_len - 1, padding="pre")

    predicted = model.predict(token_list, verbose=0)[0]

    index_to_word = {idx: word for word, idx in tokenizer.word_index.items()}
    top_indices = np.argsort(predicted)[-top_n:][::-1]
    top_words = [index_to_word.get(i, "?") for i in top_indices]
    top_probs = [float(predicted[i]) for i in top_indices]

    return top_words, top_probs


def predict_n_words(model, tokenizer, text: str, n: int, max_sequence_len: int) -> str:
    """Autoregressively predict the next N words."""
    for _ in range(n):
        words, _ = predict_top_n(model, tokenizer, text, max_sequence_len, top_n=1)
        text += " " + words[0]
    return text
