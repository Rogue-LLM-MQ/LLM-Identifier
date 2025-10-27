from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent

# load detection model
model = joblib.load(SCRIPT_DIR / "ml model/models/llm_detector.pkl")

# create FastAPI object
app = FastAPI()

class PacketData(BaseModel):
	is_post: bool
	request_content_length: float
	response_content_length: float
	response_content_size: float
	has_content_length: bool
	url_text: str
	

# when POST is sent to api /predict, run prediction code
@app.post("/predict")
def predict(data: PacketData):
	df = pd.DataFrame([data.dict()])
	pred = model.predict(df)[0]
	prob = model.predict_proba(df)[0][1]
	return {"is_llm": bool(pred), "confidence": round(float(prob), 3)}