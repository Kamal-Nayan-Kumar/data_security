"""
train_classifier.py
───────────────────
Trains a LogisticRegression classifier on CodeBERT embeddings.
Run this ONCE to produce  classifier.pkl  — then ai_analyzer.py loads it.

Usage:
    python train_classifier.py

Output:
    classifier.pkl   ← saved sklearn model
    label_report.txt ← accuracy / confusion matrix
"""

import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# ── 1. Training data ──────────────────────────────────────────────────────────
# Label 0 = SAFE   Label 1 = MALICIOUS
# Add more examples for better accuracy — at least 50 per class is ideal.

TRAINING_SAMPLES = [
    # (code_snippet, label)

    # ── SAFE examples (label = 0) ────────────────────────────────────────────
    ("def add(a, b): return a + b", 0),
    ("import os\npath = os.path.join('a','b')", 0),
    ("for i in range(10): print(i)", 0),
    ("with open('file.txt') as f: data = f.read()", 0),
    ("import json\ndata = json.loads(text)", 0),
    ("class User:\n    def __init__(self, name): self.name = name", 0),
    ("result = [x*2 for x in items if x > 0]", 0),
    ("import hashlib\nhashlib.sha256(b'data').hexdigest()", 0),
    ("try:\n    conn = db.connect()\nexcept Exception as e:\n    log(e)", 0),
    ("def validate_email(email): return '@' in email", 0),
    ("import requests\nr = requests.get('https://api.example.com/data')", 0),
    ("from datetime import datetime\nnow = datetime.utcnow()", 0),
    ("numbers = [1, 2, 3]\ntotal = sum(numbers)", 0),
    ("import logging\nlogging.basicConfig(level=logging.INFO)", 0),
    ("def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n): a, b = b, a+b\n    return a", 0),
    ("password = bcrypt.hashpw(raw.encode(), bcrypt.gensalt())", 0),
    ("import re\nif re.match(r'^[a-z]+$', username): pass", 0),
    ("df = pd.read_csv('data.csv')\nprint(df.head())", 0),
    ("SECRET = os.environ.get('SECRET_KEY')", 0),
    ("cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))", 0),

    # ── MALICIOUS examples (label = 1) ───────────────────────────────────────
    ("eval(user_input)", 1),
    ("exec(request.POST['cmd'])", 1),
    ("os.system('rm -rf /')", 1),
    ("import pickle\npickle.loads(user_data)", 1),
    ("subprocess.call(cmd, shell=True)", 1),
    ("__import__('os').system('whoami')", 1),
    ("lambda x: eval(x)(dangerous_code)", 1),
    ("api_key = 'AKIAIOSFODNN7EXAMPLE123'", 1),
    ("password = '1234'", 1),
    ("os.popen(request.args.get('cmd')).read()", 1),
    ("cursor.execute(f\"SELECT * FROM users WHERE name = '{name}'\")", 1),
    ("query = 'SELECT * FROM users WHERE 1=1'", 1),
    ("payload = '<script>alert(document.cookie)</script>'", 1),
    ("exec(base64.b64decode(encoded_payload))", 1),
    ("import ctypes\nctypes.windll.kernel32.VirtualAllocEx(...)", 1),
    ("open('/etc/passwd').read()", 1),
    ("token = 'ghp_ABCDEFabcdef1234567890ABCDEFabcdef12'", 1),
    ("data = yaml.load(user_input)  # unsafe load", 1),
    ("subprocess.Popen(['/bin/sh', '-c', user_cmd])", 1),
    ("deserialised = pickle.loads(base64.b64decode(data))", 1),
]


# ── 2. Generate embeddings ────────────────────────────────────────────────────
def get_embeddings_batch(samples):
    """Load CodeBERT once and embed all samples."""
    from transformers import AutoTokenizer, AutoModel
    import torch

    print("[*] Loading CodeBERT...")
    tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
    model = AutoModel.from_pretrained("microsoft/codebert-base")
    model.eval()
    print(f"[*] Generating embeddings for {len(samples)} samples...")

    X, y = [], []
    for code, label in samples:
        inputs = tokenizer(
            code,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        with torch.no_grad():
            outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1).numpy().flatten()
        X.append(embedding)
        y.append(label)

    return np.array(X), np.array(y)


# ── 3. Train and save ─────────────────────────────────────────────────────────
def train_and_save():
    X, y = get_embeddings_batch(TRAINING_SAMPLES)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    print("[*] Training LogisticRegression classifier...")
    clf = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=["SAFE", "MALICIOUS"])
    matrix = confusion_matrix(y_test, y_pred)

    print("\n── Classification Report ──────────────────")
    print(report)
    print("── Confusion Matrix ───────────────────────")
    print(f"                Predicted SAFE  Predicted MALICIOUS")
    print(f"Actual SAFE     {matrix[0][0]:<16} {matrix[0][1]}")
    print(f"Actual MALICIOUS{matrix[1][0]:<16} {matrix[1][1]}")

    # Save classifier
    with open("classifier.pkl", "wb") as f:
        pickle.dump(clf, f)
    print("\n[✓] Classifier saved to classifier.pkl")

    with open("label_report.txt", "w") as f:
        f.write(report)
    print("[✓] Report saved to label_report.txt")


if __name__ == "__main__":
    train_and_save()