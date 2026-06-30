"""Secret scanner tối giản, không phụ thuộc binary ngoài.

Thay thế trufflehog/git-secrets trên môi trường không cài được binary (Windows).
Dùng đúng bộ pattern trong README (Phần 6) + khóa AWS. Trả exit code != 0 nếu
phát hiện secret — phù hợp để gắn vào pre-commit hook.

Cách dùng:
    python scripts/secret_scan.py [path1 path2 ...]   # mặc định: toàn repo (git tracked)
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# (tên, regex) — bám theo README Phần 6.1
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("AWS Access Key ID", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("AWS Secret Access Key", re.compile(r"\baws_secret_access_key\b.{0,20}[A-Za-z0-9/+=]{40}", re.I)),
    ("AWS Secret (40-char)", re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])")),
    ("CCCD inline", re.compile(r"cccd[:\s]+\d{12}", re.I)),
    ("Hard-coded password", re.compile(r"""password\s*=\s*["'][^"']+["']""", re.I)),
    ("Hard-coded secret_key", re.compile(r"""secret_key\s*=\s*["'][^"']+["']""", re.I)),
    ("Private key block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----")),
]

# Bỏ qua nhị phân / thư mục môi trường
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".spacy_models", "node_modules", "reports"}
SKIP_SUFFIXES = {".pyc", ".csv", ".whl", ".tar.gz", ".png", ".jpg", ".pdf", ".key"}


def _candidate_files(args: list[str]) -> list[Path]:
    if args:
        return [Path(a) for a in args if Path(a).is_file()]
    # mặc định: file git đang theo dõi
    try:
        out = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, check=True
        ).stdout
        return [Path(p) for p in out.splitlines() if p.strip()]
    except Exception:
        return [p for p in Path(".").rglob("*") if p.is_file()]


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return hits
    for i, line in enumerate(text.splitlines(), start=1):
        # Cho phép allowlist các test vector đã biết (chuẩn detect-secrets).
        if "pragma: allowlist secret" in line:
            continue
        for name, rx in PATTERNS:
            if rx.search(line):
                hits.append((i, name, line.strip()[:100]))
    return hits


def main(argv: list[str]) -> int:
    files = _candidate_files(argv)
    total_hits = 0
    print("🔍 Secret scan — bắt đầu")
    for path in files:
        parts = set(path.parts)
        if parts & SKIP_DIRS or path.suffix in SKIP_SUFFIXES:
            continue
        for line_no, name, snippet in scan_file(path):
            total_hits += 1
            print(f"  ❌ {path}:{line_no} [{name}] {snippet}")
    if total_hits == 0:
        print("✅ Không phát hiện secret nào.")
        return 0
    print(f"\n❌ Phát hiện {total_hits} secret tiềm năng — commit nên bị chặn.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
