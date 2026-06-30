# src/quality/validation.py
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite

def build_patient_expectation_suite() -> ExpectationSuite:
    """
Tạo expectation suite cho anonymized patient data.
    """
    context = gx.get_context()
    suite = context.add_expectation_suite("patient_data_suite")

    # Lấy validator
    df = pd.read_csv("data/raw/patients_raw.csv")
    validator = context.sources.pandas_default.read_dataframe(df)

    # --- TASK: Thêm các expectations ---

    # 1. patient_id không được null
    validator.expect_column_values_to_not_be_null("patient_id")

    # 2. cccd phải có đúng 12 ký tự
    validator.expect_column_value_lengths_to_equal(
        column="cccd",
        value=12
    )

    # 3. ket_qua_xet_nghiem phải trong khoảng [0, 50]
    validator.expect_column_values_to_be_between(
        column="ket_qua_xet_nghiem",
        min_value=0,
        max_value=50
    )

    # 4. benh phải thuộc danh sách hợp lệ
    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
    validator.expect_column_values_to_be_in_set(
        column="benh",
        value_set=valid_conditions
    )

    # 5. email phải match regex pattern
    validator.expect_column_values_to_match_regex(
        column="email",
        regex=r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    # 6. Không được có duplicate patient_id
    validator.expect_column_values_to_be_unique(column="patient_id")

    validator.save_expectation_suite()
    return suite


def validate_anonymized_data(filepath: str) -> dict:
    """
Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: cột PII vẫn tồn tại sau anonymization (đã được thay thế, không bị xoá)
    expected_pii_cols = ["ho_ten", "cccd", "so_dien_thoai", "email"]
    missing_cols = [c for c in expected_pii_cols if c not in df.columns]
    if missing_cols:
        results["success"] = False
        results["failed_checks"].append(
            f"Thiếu cột PII đã anonymize: {missing_cols}"
        )

    # Check 2: Không có null trong các cột quan trọng
    critical_cols = ["patient_id", "benh", "ket_qua_xet_nghiem"]
    for col in critical_cols:
        if col in df.columns and df[col].isnull().any():
            results["success"] = False
            n = int(df[col].isnull().sum())
            results["failed_checks"].append(f"Cột '{col}' có {n} giá trị null")

    # Check 3: benh phải nằm trong danh sách hợp lệ (non-PII giữ nguyên integrity)
    valid_conditions = {"Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"}
    if "benh" in df.columns:
        invalid = set(df["benh"].dropna().unique()) - valid_conditions
        if invalid:
            results["success"] = False
            results["failed_checks"].append(f"Giá trị 'benh' không hợp lệ: {invalid}")

    results["stats"]["null_counts"] = {
        c: int(df[c].isnull().sum()) for c in df.columns
    }

    return results
