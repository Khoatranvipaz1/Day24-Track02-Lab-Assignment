# src/pii/anonymizer.py
import hashlib
import random

import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker

from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def _fake_cccd() -> str:
    """Sinh số CCCD giả 12 chữ số."""
    return "".join(random.choices("0123456789", k=12))


def _fake_phone() -> str:
    """Sinh số ĐT di động VN giả (0 + [3579/8] + 8 số)."""
    return "0" + random.choice("35789") + "".join(random.choices("0123456789", k=8))


class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N********** (che bằng '*')
        - "replace" : thay bằng fake data (dùng Faker) — mỗi entity 1 fake riêng
        - "hash"    : SHA-256 one-way hash
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        operators = {}

        if strategy == "replace":
            # Dùng operator "custom" + lambda để mỗi lần thay là 1 giá trị fake
            # mới (nếu dùng "replace"/new_value thì mọi entity cùng loại sẽ
            # nhận đúng 1 giá trị giống nhau trong cùng một text).
            operators = {
                "PERSON": OperatorConfig("custom", {"lambda": lambda x: fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: fake.email()}),
                "VN_CCCD": OperatorConfig("custom", {"lambda": lambda x: _fake_cccd()}),
                "VN_PHONE": OperatorConfig("custom", {"lambda": lambda x: _fake_phone()}),
            }
        elif strategy == "mask":
            # Che toàn bộ ký tự bằng '*' (chars_to_mask lớn => che hết).
            mask_cfg = OperatorConfig(
                "mask",
                {"masking_char": "*", "chars_to_mask": 100, "from_end": False},
            )
            operators = {
                "PERSON": mask_cfg,
                "EMAIL_ADDRESS": mask_cfg,
                "VN_CCCD": mask_cfg,
                "VN_PHONE": mask_cfg,
            }
        elif strategy == "hash":
            # SHA-256 one-way hash cho mọi entity.
            operators = {
                "DEFAULT": OperatorConfig("hash", {"hash_type": "sha256"})
            }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators if operators else None,
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email, bac_si_phu_trach): anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        text_columns = ["ho_ten", "dia_chi", "email", "bac_si_phu_trach"]
        for col in text_columns:
            if col in df_anon.columns:
                df_anon[col] = df_anon[col].astype(str).apply(self.anonymize_text)

        # Cột định danh số: thay trực tiếp bằng fake (không cần NLP).
        if "cccd" in df_anon.columns:
            df_anon["cccd"] = [_fake_cccd() for _ in range(len(df_anon))]
        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = [_fake_phone() for _ in range(len(df_anon))]

        # benh, ket_qua_xet_nghiem, patient_id: giữ nguyên (không đụng tới).
        return df_anon

    def calculate_detection_rate(self,
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công. Mục tiêu: > 95%.

        Với mỗi ô trong pii_columns, kiểm tra detect_pii() có tìm thấy
        ít nhất 1 entity hay không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
