"""
email_parser.py
Parses uploaded .txt and .eml files and returns plain-text email content.
"""

import email
import email.policy
from email import message_from_bytes


SUPPORTED_EXTENSIONS = {".txt", ".eml"}


def parse_file(filename: str, file_bytes: bytes) -> str:
    """
    Parse an uploaded file and return its text content.

    Parameters
    ----------
    filename  : original filename (used to determine extension)
    file_bytes: raw file bytes

    Returns
    -------
    str  — plain-text email content (subject + body)

    Raises
    ------
    ValueError  if the file extension is not supported
    """
    ext = _get_extension(filename)

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Only {', '.join(sorted(SUPPORTED_EXTENSIONS))} files are accepted."
        )

    if ext == ".txt":
        return _parse_txt(file_bytes)

    if ext == ".eml":
        return _parse_eml(file_bytes)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_extension(filename: str) -> str:
    """Return the lowercase file extension including the dot."""
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def _parse_txt(file_bytes: bytes) -> str:
    """Decode a plain-text file, trying UTF-8 then Latin-1 as a fallback."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


def _parse_eml(file_bytes: bytes) -> str:
    """
    Parse an RFC 2822 .eml file.
    Extracts the Subject header and the plain-text body.
    If only HTML is available, strips the tags.
    """
    msg = message_from_bytes(file_bytes, policy=email.policy.default)

    subject = msg.get("Subject", "")
    body = ""

    if msg.is_multipart():
        # Walk all parts, prefer text/plain
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition:
                continue

            if content_type == "text/plain":
                body = part.get_content()
                break
            elif content_type == "text/html" and not body:
                body = _strip_html(part.get_content())
    else:
        content_type = msg.get_content_type()
        raw = msg.get_content()
        if content_type == "text/html":
            body = _strip_html(raw)
        else:
            body = raw

    parts = []
    if subject:
        parts.append(f"Subject: {subject}")
    if body:
        parts.append(body.strip())

    return "\n\n".join(parts)


def _strip_html(html: str) -> str:
    """Very lightweight HTML tag stripper using regex (no external deps)."""
    import re
    # Remove script / style blocks entirely
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Strip remaining tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    html = re.sub(r"\s+", " ", html).strip()
    return html
