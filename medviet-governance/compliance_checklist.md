# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [ ] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [ ] Backup cũng phải ở trong lãnh thổ VN
- [ ] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [ ] Thu thập consent trước khi dùng data cho AI training
- [ ] Có mechanism để user rút consent (Right to Erasure)
- [ ] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [ ] Có incident response plan
- [ ] Alert tự động khi phát hiện breach
- [ ] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.vn (hotline nội bộ: ext. 113)

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256-GCM at rest (envelope/SimpleVault), TLS 1.3 in transit | ✅ Done | Infra Team |
| Audit logging | Structured access logs (JSON) + immutable WORM store | ✅ Done | Platform Team |
| Breach detection | Anomaly monitoring (Prometheus + Grafana alerts) | ✅ Done | Security Team |

## F. Chi tiết technical solution cho các control còn lại

### Encryption (AES-256 at rest, TLS 1.3 in transit)
- **At rest:** Envelope encryption qua `src/encryption/vault.py` (`SimpleVault`):
  KEK (256-bit) bọc DEK (256-bit/record), data mã hoá bằng AES-256-GCM.
  Production: thay KEK file bằng **AWS KMS / HashiCorp Vault** (HSM-backed).
- **In transit:** Bắt buộc TLS 1.3 ở reverse proxy (nginx/Envoy), HSTS bật,
  từ chối cipher < TLS 1.2; mTLS giữa các service nội bộ.

### Audit logging (CloudTrail + API access logs)
- Mỗi request qua FastAPI ghi log có cấu trúc: `timestamp, user, role,
  resource, action, decision (allow/deny), request_id` — KHÔNG log PII.
- Lưu log vào kho **append-only/WORM** (vd: S3 Object Lock hoặc Loki immutable),
  giữ tối thiểu 12 tháng, đồng bộ với CloudTrail nếu chạy trên AWS.
- Log được ship sang SIEM để truy vết & phục vụ điều tra sự cố.

### Breach detection (Anomaly monitoring)
- **Prometheus** thu metric: tỉ lệ HTTP 401/403, số lần truy cập raw PII,
  volume export bất thường, request theo IP/role.
- **Grafana alert / Alertmanager**: cảnh báo khi 403 spike, hoặc 1 user đọc
  > N record/phút → kích hoạt incident response, gửi cảnh báo trong < 5 phút
  để đảm bảo kịp deadline báo cáo 72h của NĐ13.
