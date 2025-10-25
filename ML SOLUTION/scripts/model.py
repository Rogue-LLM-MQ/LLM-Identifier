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

# load dataset
if not CSV_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

df = pd.read_csv(CSV_PATH)

# normalise paths by removing random noise (ie. long id's and hashes)
def preprocess_path(path):
    path = path.lower()
    path = path.replace("/", " / ")
    path = re.sub(r"([a-z])([A-Z])", r"\1 \2", path)
    path = re.sub(r"[\._]", " ", path)
    return path

# ensure filename's have text, and apply normalisation function
df["filename"] = df["filename"].fillna("")
df["url_text"] = df["filename"].apply(preprocess_path)

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

X = balanced_df[numeric_cols + ["url_text"]]
y = balanced_df["is_llm"].astype(int)

# use tf-idf on filename, with regex token to detect typical path format
tfidf = TfidfVectorizer(
    lowercase=True,
    token_pattern=r"[a-zA-Z][a-zA-Z0-9_\-]{2,}",
    max_features=100
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

# etract trained components
classifier = model.named_steps["classifier"]
preprocessor = model.named_steps["preprocessor"]

# get numeric feature names from ColumnTransformer
numeric_feature_names = preprocessor.transformers_[0][2]

# get TF-IDF feature names
tfidf = preprocessor.named_transformers_["txt"]
tfidf_feature_names = tfidf.get_feature_names_out()

# combine all feature names in correct order
feature_names = list(numeric_feature_names) + list(tfidf_feature_names)

# extract coefficients
coefs = classifier.coef_[0]

# split numeric vs text importance
numeric_count = len(numeric_feature_names)
text_coefs = coefs[numeric_count:]
numeric_coefs = coefs[:numeric_count]

print("CLASSIFICATION REPORT")
print(classification_report(y_test, y_pred))

# print numeric features in descending importance
print("\n===== NUMERIC FEATURE IMPORTANCE =====")
for name, coef in sorted(zip(numeric_feature_names, numeric_coefs), key=lambda x: abs(x[1]), reverse=True):
    print(f"{name:<50} {coef:.3f}")

# print top llm and non-llm tfidf tokens
top_n = 20
top_indices = np.argsort(text_coefs)[-top_n:]
bottom_indices = np.argsort(text_coefs)[:top_n]

print("\n===== TOP TOKENS ASSOCIATED WITH LLM TRAFFIC =====")
for i in reversed(top_indices):
    print(f"{tfidf_feature_names[i]:<50} {text_coefs[i]:.3f}")

print("\n===== TOP TOKENS ASSOCIATED WITH NON-LLM TRAFFIC =====")
for i in bottom_indices:
    print(f"{tfidf_feature_names[i]:<50} {text_coefs[i]:.3f}")