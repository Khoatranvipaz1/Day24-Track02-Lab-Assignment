# src/pii/detector.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

# Các entity chuẩn của pipeline MedViet
SUPPORTED_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]

# spaCy KHÔNG có model "vi_core_news_lg" chính thức -> thử lần lượt, model nào
# load được thì dùng. "xx_ent_wiki_sm" là model đa ngôn ngữ có nhãn PER (PERSON).
_CANDIDATE_MODELS = ["vi_core_news_lg", "xx_ent_wiki_sm"]

# Bảng chữ HOA/thường tiếng Việt (re chuẩn không hỗ trợ \p{Lu}).
_VN_UPPER = "A-ZĐÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ"
_VN_LOWER = "a-zđàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ"
# Họ tên VN: 2–4 từ viết hoa liên tiếp (vd "Nguyễn Văn An").
_VN_NAME_REGEX = rf"\b[{_VN_UPPER}][{_VN_LOWER}]+(?:\s+[{_VN_UPPER}][{_VN_LOWER}]+){{1,3}}\b"


def _build_nlp_engine():
    """Tạo spaCy NLP engine, chỉ dùng model đã được cài sẵn.

    Lưu ý: presidio sẽ tự gọi `spacy download` (SystemExit) nếu model thiếu,
    nên ta kiểm tra `spacy.util.is_package` trước để chọn model có sẵn.
    """
    import spacy.util

    for model_name in _CANDIDATE_MODELS:
        if spacy.util.is_package(model_name):
            provider = NlpEngineProvider(nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "vi", "model_name": model_name}],
            })
            return provider.create_engine()
    raise RuntimeError(
        "Không tìm thấy spaCy model nào cho tiếng Việt. "
        "Hãy chạy: python -m spacy download xx_ent_wiki_sm"
    )


def build_vietnamese_analyzer() -> AnalyzerEngine:
    """
    Xây dựng AnalyzerEngine với các recognizer tùy chỉnh cho VN.
    """

    # --- TASK 2.2.1 ---
    # CCCD recognizer: số CCCD VN có đúng 12 chữ số (word-boundary để không
    # "ăn" nhầm vào một dãy số dài hơn).
    cccd_pattern = Pattern(
        name="cccd_pattern",
        regex=r"\b\d{12}\b",
        score=0.9
    )
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        supported_language="vi",
        patterns=[cccd_pattern],
        context=["cccd", "căn cước", "chứng minh", "cmnd"]
    )

    # --- TASK 2.2.2 ---
    # Phone recognizer: số ĐT di động VN = 0 + (3|5|7|8|9) + 8 chữ số = 10 số.
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        supported_language="vi",
        patterns=[Pattern(
            name="vn_phone",
            regex=r"\b0[35789]\d{8}\b",
            score=0.85
        )],
        context=["điện thoại", "sdt", "phone", "liên hệ"]
    )

    # Custom PERSON recognizer cho họ tên tiếng Việt — bổ sung cho spaCy NER
    # (model đa ngôn ngữ nhận tên VN đứng một mình khá yếu). Score vừa phải
    # để NER thắng khi cả hai cùng bắt.
    vn_person_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        supported_language="vi",
        patterns=[Pattern(name="vn_full_name", regex=_VN_NAME_REGEX, score=0.6)],
        context=["bệnh nhân", "họ tên", "bác sĩ", "ông", "bà"],
    )

    # --- TASK 2.2.3 ---
    # NLP engine dùng spaCy model (vi_core_news_lg nếu có, fallback xx_ent_wiki_sm).
    nlp_engine = _build_nlp_engine()

    # --- TASK 2.2.4 ---
    # Khởi tạo AnalyzerEngine và add các recognizer tùy chỉnh.
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["vi"],
    )
    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(vn_person_recognizer)

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """
    Detect PII trong text tiếng Việt.
    Trả về list các RecognizerResult.
    Entities: PERSON, EMAIL_ADDRESS, VN_CCCD, VN_PHONE
    """
    results = analyzer.analyze(
        text=text,
        language="vi",
        entities=SUPPORTED_ENTITIES,
    )
    return results
