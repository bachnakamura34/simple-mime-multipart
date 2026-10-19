import re


def _format_boundary(boundary):
    """Return the boundary delimiter line for the given boundary string."""
    return "--" + boundary


def _normalize_header_name(name):
    """Lowercase header names to achieve case-insensitive comparison."""
    return name.strip().lower()


def _parse_part_headers(lines):
    """Parse a list of raw header lines into a header dict (names lowercased).

    Header lookups are case-insensitive: the returned dict supports access by
    any casing of the header name.
    """
    headers = {}
    for line in lines:
        if ":" not in line:
            continue
        name, _, value = line.partition(":")
        headers[_normalize_header_name(name)] = value.strip()
    return _CaseInsensitiveDict(headers)


class _CaseInsensitiveDict(dict):
    """A dict subclass permitting case-insensitive key lookups.

    Keys are stored in their normalized (lowercased) form, but lookups by any
    casing of the same name return the stored value.
    """

    def __contains__(self, key):
        return super().__contains__(key.strip().lower() if isinstance(key, str) else key)

    def __getitem__(self, key):
        return super().__getitem__(key.strip().lower() if isinstance(key, str) else key)

    def get(self, key, default=None):
        return super().get(key.strip().lower() if isinstance(key, str) else key, default)


def _split_headers_body(block_lines):
    """Split a raw part block into header lines and body lines at the first blank line."""
    for idx, line in enumerate(block_lines):
        if line == "":
            return block_lines[:idx], block_lines[idx + 1:]
    return block_lines, []


def _is_terminator(line, boundary):
    """Return True if the line is the closing boundary delimiter."""
    return line == "--" + boundary + "--"


def _is_delimiter(line, boundary):
    """Return True if the line is an inner or closing boundary delimiter."""
    if line == "--" + boundary:
        return True
    if line == "--" + boundary + "--":
        return True
    return False


def parse_multipart(body, boundary):
    """Parse a multipart MIME body into a list of part dictionaries.

    Each returned part is a dict with keys:
      - headers: dict of header name -> value (names lowercased)
      - body: bytes containing the part content

    The leading CRLF before each boundary line is consumed and not included
    in the preceding part's body, per RFC 2046 section 5.1.1. We split on
    the boundary line itself rather than a regex so that binary content
    containing boundary-like byte sequences is not mis-split; only a line
    matching the boundary exactly triggers a split.

    We do not attempt transfer-encoding (e.g. base64) decoding. Callers
    must decode part bodies according to the part's Content-Encoding or
    Content-Transfer-Encoding header themselves. Keeping this step out of
    the parser avoids guessing encoding semantics that the caller knows
    better.
    """
    if not boundary:
        raise ValueError("boundary must be a non-empty string")

    text = body.decode("utf-8", errors="replace")
    lines = text.split("\r\n")

    parts = []
    current_lines = None
    seen_terminator = False

    for line in lines:
        if _is_delimiter(line, boundary):
            if current_lines is not None:
                header_lines, body_lines = _split_headers_body(current_lines)
                headers = _parse_part_headers(header_lines)
                body_text = "\r\n".join(body_lines)
                parts.append({
                    "headers": headers,
                    "body": body_text.encode("utf-8"),
                })
            current_lines = []
            if _is_terminator(line, boundary):
                seen_terminator = True
                break
        else:
            if current_lines is not None:
                current_lines.append(line)

    if not seen_terminator:
        raise ValueError("multipart body missing closing boundary")

    return parts
