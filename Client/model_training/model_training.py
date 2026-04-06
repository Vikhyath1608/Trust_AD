import os
import json
import numpy as np
from pathlib import Path
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# ================================
# CONFIG
# ================================

TRAINING_DATA_PATH = "./training_data.json"
MODEL_PATH = "./ml_product_model.pkl"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TEST_SIZE = 0.2
RANDOM_STATE = 42

# ================================
# LOAD TRAINING DATA
# ================================

def load_training_data(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Training data not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    if not entries:
        raise ValueError("No training entries found")

    texts = []
    labels = []

    for e in entries:
        if "query" in e and "label" in e:
            texts.append(e["query"].strip())
            labels.append(int(e["label"]))

    return texts, np.array(labels)

# ================================
# MAIN TRAINING FUNCTION
# ================================

def train_model():
    print("\nTraining Product Classification Model")
    print("=" * 60)

    # Load data
    texts, labels = load_training_data(TRAINING_DATA_PATH)
    print(f" Loaded {len(texts)} training samples")

    # Load embedding model
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # Generate embeddings
    print(" Generating embeddings...")
    X = embedder.encode(texts, convert_to_numpy=True)
    y = labels

    # Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    # Train classifier
    print(" Training Logistic Regression classifier...")
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("\n Evaluation Results")
    print("-" * 60)
    print(f"Accuracy: {acc:.4f}\n")
    print(classification_report(y_test, y_pred, target_names=["Non-Product", "Product"]))

    # Save model
    joblib.dump(clf, MODEL_PATH)
    print(f"\nModel saved to: {MODEL_PATH}")
    print("=" * 60)

# ================================
# ENTRY POINT
# ================================

if __name__ == "__main__":
    train_model()