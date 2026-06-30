# Lab #24 — Data Governance & Security for AI Platform

**Sinh viên:** Trần Văn Khoa
**MSSV:** 2A202600827
**Khóa học:** AICB-P2T2 · Lab #24 Extended
**Ngày nộp:** 2026-06-30

---

## Checklist Deliverables

| Hạng mục | Điểm | Trạng thái | Bằng chứng |
|---|---|---|---|
| PII Detection (≥95%) | 25 | ✅ Đạt | `reports/test_results.txt` (6/6 pass) |
| Anonymization | 20 | ✅ Đạt | `data/processed/patients_anonymized.csv` |
| RBAC API (401/403) | 20 | ✅ Đạt | `src/access/`, `src/api/main.py` |
| Encryption (envelope) | 15 | ✅ Đạt | `src/encryption/vault.py` (round-trip OK) |
| Security Audit | 10 | ✅ Đạt | `reports/SECURITY_AUDIT.md`, `bandit_report.json` |
| Compliance Checklist | 10 | ✅ Đạt | `compliance_checklist.md` |

**Bonus:** Phần 6 — Agent Governance (Microsoft AGT) chạy thật trong notebook `data-governance-lab/`.

## Cách chạy

```bash
cd medviet-governance
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
python -m spacy download xx_ent_wiki_sm          # NER tiếng Việt (fallback)
pip install pyvi

python scripts/generate_data.py                  # tạo dữ liệu
pytest tests/ -v                                 # 6/6 pass
uvicorn src.api.main:app --reload                # API + RBAC
```

## Kết quả kiểm thử (đã verify)
- pytest: **6/6 PASSED**, detection rate **≥95%**
- RBAC: admin/ml_engineer/data_analyst/intern hoạt động đúng, **403 đúng chỗ**
- Encryption: envelope AES-256-GCM round-trip thành công
- Bandit: **0 HIGH/MED/LOW**; secret scan: **0 secret**, chặn được fake credential
