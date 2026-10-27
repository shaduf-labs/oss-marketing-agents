"""Offline advertised-header comparison for invented messages; not RFC compliance."""
import argparse
from email import policy
from email.parser import BytesParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
PAIR = "List-Unsubscribe=One-Click"
ANGLE_ITEM = re.compile(r"<([^<>\s]+)>")


def one_https_uri(value):
    """Return (URI, error); allow optional mailto but exactly one HTTPS URI."""
    parts = [part.strip() for part in value.split(",")]
    uris = []
    if not parts or any(not ANGLE_ITEM.fullmatch(part) for part in parts):
        return None, True
    for part in parts:
        uri = part[1:-1]
        try:
            parsed = urlsplit(uri)
        except ValueError:
            return None, True
        if parsed.scheme.lower() == "mailto" and len(parts) > 1:
            continue
        try:
            invalid = (parsed.scheme != "https" or not parsed.hostname
                       or parsed.username or parsed.password or parsed.port
                       or parsed.fragment or not parsed.path)
        except ValueError:  # Invalid authority/port is malformed, not a crash.
            return None, True
        if invalid:
            return None, True
        uris.append(uri)
    return (uris[0], False) if len(uris) == 1 else (None, True)


def inspect(case, mapping):
    if case not in mapping["cases"]:
        raise ValueError("unknown case")
    campaign = mapping["cases"][case]
    expected = mapping["campaigns"][campaign]
    raw = (HERE / "messages" / (case + ".eml")).read_bytes()
    message = BytesParser(policy=policy.default).parsebytes(raw)
    issues = []
    uri = None
    # This fixture is intentionally strict: defects, bare LF or no body separator
    # cannot be treated as an inspectable pre-send message.
    if message.defects or b"\r\n\r\n" not in raw or re.search(rb"(?<!\r)\n", raw):
        issues.append("malformed_message")
    unsubscribe = message.get_all("List-Unsubscribe", [])
    post = message.get_all("List-Unsubscribe-Post", [])
    if len(unsubscribe) == 0:
        issues.append("missing_list_unsubscribe")
    elif len(unsubscribe) > 1:
        issues.append("duplicate_list_unsubscribe")
    else:
        uri, bad = one_https_uri(str(unsubscribe[0]))
        if bad:
            issues.append("malformed_list_unsubscribe_uri")
        elif "/one-click/all/" in urlsplit(uri).path:
            issues.append("global_route")
        elif uri != expected["one_click_uri"]:
            other_campaign_uri = {
                name: item["one_click_uri"]
                for name, item in mapping["campaigns"].items() if name != campaign
            }
            issues.append("wrong_list_route" if uri in other_campaign_uri.values()
                          else "wrong_endpoint")
    if len(post) == 0:
        issues.append("missing_list_unsubscribe_post")
    elif len(post) > 1:
        issues.append("duplicate_list_unsubscribe_post")
    elif str(post[0]).strip() != PAIR:
        issues.append("malformed_list_unsubscribe_post")
    return {
        "case": case,
        "campaign": campaign,
        "expected_list": expected["list"],
        "observed_uri": uri,
        "pass": not issues,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", default=str(HERE / "expected-mapping.json"))
    parser.add_argument("--case", required=True)
    args = parser.parse_args()
    mapping = json.loads(Path(args.mapping).read_text())
    try:
        result = inspect(args.case, mapping)
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"case": args.case, "pass": False,
                          "issues": ["fixture_error"], "error": str(exc)}, sort_keys=True))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
