# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

RAW_CSV = "data/raw/patients_raw.csv"


# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv, trả về 10 records đầu tiên.
    """
    df = pd.read_csv(RAW_CSV)
    return JSONResponse({
        "requested_by": current_user["username"],
        "count": 10,
        "data": df.head(10).to_dict(orient="records"),
    })


# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    df = pd.read_csv(RAW_CSV).head(10)
    df_anon = anonymizer.anonymize_dataframe(df)
    return JSONResponse({
        "requested_by": current_user["username"],
        "count": len(df_anon),
        "data": df_anon.to_dict(orient="records"),
    })


# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Số bệnh nhân theo từng loại bệnh — KHÔNG chứa PII.
    """
    df = pd.read_csv(RAW_CSV)
    counts = df["benh"].value_counts().to_dict()
    return JSONResponse({
        "requested_by": current_user["username"],
        "total_patients": int(len(df)),
        "by_condition": {k: int(v) for k, v in counts.items()},
        "avg_test_result": round(float(df["ket_qua_xet_nghiem"].mean()), 2),
    })


# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Chỉ admin được xóa. Các role khác nhận 403 (do require_permission).
    """
    return JSONResponse({
        "deleted": patient_id,
        "deleted_by": current_user["username"],
        "status": "ok",
    })


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
