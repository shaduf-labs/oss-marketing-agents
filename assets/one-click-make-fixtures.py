"""Write only invented local RFC 5322/MIME bytes; no sending or network."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "messages"
OUT.mkdir(exist_ok=True)

A = "https://unsubscribe.example.invalid/one-click/newsletter-a/token-a-001"
B = "https://unsubscribe.example.invalid/one-click/newsletter-b/token-b-001"
GLOBAL = "https://unsubscribe.example.invalid/one-click/all/token-a-001"
POST = "List-Unsubscribe=One-Click"

CASES = {
    "valid-a": ("a", [f"List-Unsubscribe: <{A}>", f"List-Unsubscribe-Post: {POST}"]),
    "valid-b": ("b", [f"List-Unsubscribe: <{B}>", f"List-Unsubscribe-Post: {POST}"]),
    "cross-a-to-b": ("a", [f"List-Unsubscribe: <{B}>", f"List-Unsubscribe-Post: {POST}"]),
    "global-a": ("a", [f"List-Unsubscribe: <{GLOBAL}>", f"List-Unsubscribe-Post: {POST}"]),
    "missing-uri-a": ("a", [f"List-Unsubscribe-Post: {POST}"]),
    "missing-post-b": ("b", [f"List-Unsubscribe: <{B}>"]),
    "duplicate-uri-a": ("a", [f"List-Unsubscribe: <{A}>", f"List-Unsubscribe: <{A}>", f"List-Unsubscribe-Post: {POST}"]),
    "duplicate-post-b": ("b", [f"List-Unsubscribe: <{B}>", f"List-Unsubscribe-Post: {POST}", f"List-Unsubscribe-Post: {POST}"]),
    "malformed-uri-a": ("a", ["List-Unsubscribe: <http://unsubscribe.example.invalid/one-click/newsletter-a/token-a-001>", f"List-Unsubscribe-Post: {POST}"]),
    "malformed-post-b": ("b", [f"List-Unsubscribe: <{B}>", "List-Unsubscribe-Post: List-Unsubscribe=One-Click; other=yes"]),
    "multiple-https-a": ("a", [f"List-Unsubscribe: <{A}>, <{B}>", f"List-Unsubscribe-Post: {POST}"]),
}

for case, (list_letter, special) in CASES.items():
    headers = [
        f"From: Fictional Lists <sender@newsletter.example.invalid>",
        f"To: Fictional Reader <reader@recipient.example.invalid>",
        f"Date: Mon, 26 Oct 2026 10:00:00 +0000",
        f"Message-ID: <{case}@newsletter.example.invalid>",
        f"Subject: Fictional Newsletter {list_letter.upper()} -- {case}",
        "MIME-Version: 1.0",
        "Content-Type: text/plain; charset=utf-8",
        "Content-Transfer-Encoding: 8bit",
        *special,
    ]
    body = (
        f"Invented {list_letter.upper()} message; never send.\r\n"
        "Optional body preference link: "
        "https://preferences.example.invalid/account/all\r\n"
    )
    payload = ("\r\n".join(headers) + "\r\n\r\n" + body).encode("utf-8")
    (OUT / f"{case}.eml").write_bytes(payload)
print(f"wrote {len(CASES)} fictional message files to messages/")
