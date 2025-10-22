from pathlib import Path
import re
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.utils import resample
from sklearn.metrics import classification_report

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CSV_PATH = DATA_DIR / "har_combined_dataset.csv"

if not CSV_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

print(f"📂 Loading dataset: {CSV_PATH}")
df = pd.read_csv(CSV_PATH)

# normalise paths by removing random noise (ie. long id's and hashes)
def normalize_path(path):
    path = str(path)
    path = re.sub(r"[a-f0-9]{8,}", "ID", path)
    path = re.sub(r"\d+", "NUM", path)
    path = re.sub(r"https?://[^/]+", "", path)
    return path

# ensure filename's have text, and apply normalisation function
df["filename"] = df["filename"].fillna("")
df["url_text"] = df["filename"].apply(normalize_path)

# set numeric features, and fill empty values with 0
numeric_cols = [
    "request_content_length",
    "response_content_length",
    "response_content_size",
    "has_content_length",
    "is_post"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["is_llm"] = df["is_llm"].astype(str).str.lower().isin(["true", "1", "yes"])

# balance dataset to remove class bias
llm_df = df[df["is_llm"] == True]
non_llm_df = df[df["is_llm"] == False]

non_llm_down = resample(
    non_llm_df,
    replace=False,
    n_samples=len(llm_df),
    random_state=42
)

balanced_df = pd.concat([llm_df, non_llm_down]).sample(frac=1, random_state=42)
print(f"✅ Balanced dataset: {len(balanced_df)} samples")

X = balanced_df[numeric_cols + ["url_text"]]
y = balanced_df["is_llm"].astype(int)

# use tf-idf on filename, with regex token to detect typical path format
tfidf = TfidfVectorizer(
    lowercase=True,
    token_pattern=r"[a-zA-Z0-9_\-\/\.=?&]+",
    max_features=1000
)

# set preprocessor, combining numeric and text features
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_cols),
        ("txt", tfidf, "url_text"),
    ]
)

# create logistic regression model
model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        max_iter=500,
        class_weight="balanced"
    ))
])

# train model
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

# print performance metrics

print("\n CLASSIFICATION REPORT")
print(classification_report(y_test, y_pred, digits=3))

# print top tf-idf tokens for both llm and non-llm paths
tfidf_vectorizer = model.named_steps["preprocessor"].named_transformers_["txt"]
feature_names = tfidf_vectorizer.get_feature_names_out()
coefs = model.named_steps["classifier"].coef_[0]

top_positive_idx = np.argsort(coefs)[-20:]
top_negative_idx = np.argsort(coefs)[:20]

print("\n TOP TOKENS - LLM")
for i in top_positive_idx:
    print(f"{feature_names[i]:<50} {coefs[i]:.3f}")

print("\n TOP TOKENS - NON-LLM")
for i in top_negative_idx:
    print(f"{feature_names[i]:<50} {coefs[i]:.3f}")