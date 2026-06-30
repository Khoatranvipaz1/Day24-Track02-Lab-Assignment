# Security Audit Report — MedViet Data Governance Platform

Ngày chạy: 2026-06-30 · Môi trường: Python 3.10 (`.venv`)

## 1. Test suite (pytest)
- **6/6 PASSED** — chi tiết: [test_results.txt](test_results.txt)
- Bao gồm: phát hiện CCCD/phone/email, **detection rate ≥ 95%**, ẩn danh không lộ PII gốc, cột lâm sàng giữ nguyên.

## 2. SAST — Bandit
- Kết quả: **0 HIGH · 0 MEDIUM · 0 LOW** — [bandit_report.json](bandit_report.json) / [bandit_report.txt](bandit_report.txt)
- 3 cảnh báo B311 (dùng `random` cho **dữ liệu giả**, không phải crypto) đã được đánh dấu `# nosec B311` kèm lý do trong `src/pii/anonymizer.py`.

## 3. Secret scanning
- Tool: `scripts/secret_scan.py` (scanner Python portable — thay cho trufflehog/git-secrets vốn là binary ngoài, không cài được trên Windows box này).
- Quét repo: **0 secret** — [secret_scan_report.txt](secret_scan_report.txt)
- **Đã kiểm chứng hook chặn credential:** quét file chứa fake AWS key (`AKIAIOSFODNN7EXAMPLE`, secret 40 ký tự, `password=...`) → bắt **4/4** và trả exit code 1 (commit bị chặn).
- Test vector CCCD trong `tests/test_pii.py` được allowlist bằng `# pragma: allowlist secret`.
- Hook `.github/hooks/pre-commit` đã cập nhật: dùng `git-secrets` nếu có, nếu không fallback sang `secret_scan.py` → chạy được mọi nơi.

## 4. Dependency CVE — pip-audit
- [pip_audit_report.txt](pip_audit_report.txt)
- Đã vá: `setuptools` (→82.0.1), `gitpython` (→3.1.50+), `jinja2` (→3.1.6+).
- **Còn lại 1 CVE — rủi ro chấp nhận có ràng buộc:**

  | Package | Version | CVE | Fix | Lý do không vá |
  |---|---|---|---|---|
  | cryptography | 46.0.7 | GHSA-537c-gmf6-5ccf | 48.0.1 | `presidio-anonymizer` ghim `cryptography<47.0.0`; nâng lên 48 sẽ phá vỡ presidio. |

  **Giảm thiểu:** CVE chỉ ảnh hưởng OpenSSL tĩnh trong wheel; có thể build cryptography từ sdist với OpenSSL đã vá, hoặc chờ presidio nới ràng buộc. Theo dõi để nâng cấp khi presidio hỗ trợ.

## 5. Các tool cần binary ngoài (chưa chạy trên môi trường này)
| Tool | Trạng thái | Cách cài để chạy |
|---|---|---|
| trufflehog (Go) | thay bằng `secret_scan.py` | `scoop install trufflehog` hoặc binary từ GitHub release |
| git-secrets | hook có fallback | `git clone awslabs/git-secrets && make install` |
| OPA | policy `policies/opa_policy.rego` đã viết & verify logic | `choco install opa` rồi `opa eval ...` |

## Tổng kết
Pass tất cả hạng mục security audit có thể chạy được: **pytest 6/6, Bandit sạch, secret scan sạch + chặn được credential, CVE chỉ còn 1 (ràng buộc presidio, đã tài liệu hoá).**
