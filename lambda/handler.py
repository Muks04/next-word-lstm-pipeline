import json
import os
import pickle
import numpy as np
import boto3

# Cached across warm invocations
_model = None
_tokenizer = None

S3_BUCKET     = os.environ["S3_BUCKET"]
MODEL_KEY     = os.environ.get("MODEL_KEY", "models/next_word_lstm_model_with_early_stopping.h5")
TOKENIZER_KEY = os.environ.get("TOKENIZER_KEY", "models/tokenizer.pickle")
MODEL_PATH     = "/tmp/model.h5"
TOKENIZER_PATH = "/tmp/tokenizer.pickle"


def _load_artifacts():
    global _model, _tokenizer
    if _model is None:
        import tensorflow as tf
        from tensorflow.keras.models import load_model

        s3 = boto3.client("s3")

        # Download model
        s3.download_file(S3_BUCKET, MODEL_KEY, MODEL_PATH)

        # Download tokenizer
        s3.download_file(S3_BUCKET, TOKENIZER_KEY, TOKENIZER_PATH)

        # Custom LSTM to handle version mismatch
        class CompatibleLSTM(tf.keras.layers.LSTM):
            def __init__(self, *args, **kwargs):
                kwargs.pop("time_major", None)
                super().__init__(*args, **kwargs)

        _model = load_model(
            MODEL_PATH,
            custom_objects={"LSTM": CompatibleLSTM},
            compile=False,
        )

        with open(TOKENIZER_PATH, "rb") as f:
            _tokenizer = pickle.load(f)


def _predict_top_n(text: str, top_n: int = 10):
    from tensorflow.keras.preprocessing.sequence import pad_sequences

    max_sequence_len = _model.input_shape[1] + 1
    token_list = _tokenizer.texts_to_sequences([text])[0]

    if len(token_list) >= max_sequence_len:
        token_list = token_list[-(max_sequence_len - 1):]

    token_list = pad_sequences([token_list], maxlen=max_sequence_len - 1, padding="pre")
    predicted = _model.predict(token_list, verbose=0)[0]

    index_to_word = {idx: word for word, idx in _tokenizer.word_index.items()}
    top_indices = np.argsort(predicted)[-top_n:][::-1]

    return [
        {"word": index_to_word.get(int(i), "?"), "probability": round(float(predicted[i]), 6)}
        for i in top_indices
    ]


def handler(event, context):
    try:
        # Support both direct invoke and API Gateway
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", event)

        text  = body.get("text", "").strip()
        top_n = int(body.get("top_n", 10))

        if not text:
            return _response(400, {"error": "text field is required"})

        _load_artifacts()
        predictions = _predict_top_n(text, top_n)

        return _response(200, {
            "input": text,
            "predictions": predictions,
            "top_word": predictions[0]["word"],
            "confidence": predictions[0]["probability"],
        })

    except Exception as e:
        return _response(500, {"error": str(e)})


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
