# src/quality/validation.py
import pandas as pd
import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations import ExpectationSuite

def build_patient_expectation_suite() -> ExpectationSuite:
    """Tạo expectation suite cho patient data (Great Expectations 1.x API).

    Thêm 6 expectations và chạy validate trên dữ liệu raw.
    """
    context = gx.get_context()  # ephemeral context

    # Đăng ký nguồn pandas + batch từ DataFrame (đọc cccd dạng str giữ số 0 đầu)
    df = pd.read_csv(
        "data/raw/patients_raw.csv",
        dtype={"cccd": str, "so_dien_thoai": str},
    )
    data_source = context.data_sources.add_pandas(name="medviet_pandas")
    asset = data_source.add_dataframe_asset(name="patients")
    batch_def = asset.add_batch_definition_whole_dataframe("batch_def")

    # Tạo suite + 6 expectations
    suite = context.suites.add(ExpectationSuite(name="patient_data_suite"))

    # 1. patient_id không được null
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="patient_id"))
    # 2. cccd phải có đúng 12 ký tự
    suite.add_expectation(gxe.ExpectColumnValueLengthsToEqual(column="cccd", value=12))
    # 3. ket_qua_xet_nghiem phải trong khoảng [0, 50]
    suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(
        column="ket_qua_xet_nghiem", min_value=0, max_value=50))
    # 4. benh phải thuộc danh sách hợp lệ
    suite.add_expectation(gxe.ExpectColumnValuesToBeInSet(
        column="benh",
        value_set=["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]))
    # 5. email phải match regex pattern
    suite.add_expectation(gxe.ExpectColumnValuesToMatchRegex(
        column="email", regex=r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"))
    # 6. Không được có duplicate patient_id
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="patient_id"))

    # Chạy validate để chứng minh suite hoạt động
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})
    validation_result = batch.validate(suite)
    print(f"GE validation success: {validation_result.success}")

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
