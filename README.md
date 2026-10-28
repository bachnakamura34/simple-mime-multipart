# simple-mime-multipart

Parses RFC 2046 multipart MIME bodies into a list of part dictionaries, each with lowercased headers and a bytes body.

## Usage

```python
from simple_mime_multipart import parse_multipart

body = (
    b"--BOUNDARY\r\n"
    b"Content-Type: text/plain\r\n"
    b"\r\n"
    b"Hello, world!\r\n"
    b"--BOUNDARY--\r\n"
)
parts = parse_multipart(body, "BOUNDARY")
# parts[0]["headers"]["content-type"] == "text/plain"
# parts[0]["body"] == b"Hello, world!"
```

## Why this exists

There are many MIME parsers, but most either live inside a heavy framework or handle transfer-encoding (base64, quoted-printable) in ways that make assumptions about your data. This library does one thing: it splits a multipart body on boundary delimiter lines and hands you the raw part content as bytes. You decide how to decode it.

The trade-off: no transfer-encoding decoding is performed. If a part has `Content-Transfer-Encoding: base64`, `parts[0]["body"]` will be the base64 text, not the decoded bytes. This keeps the parser predictable and lets you apply the decoding your application actually needs.

## Edge cases worth knowing

- The boundary must match a full line exactly. A line that merely contains the boundary as a substring will not cause a split; only a line equal to `--BOUNDARY` or `--BOUNDARY--` triggers a delimiter.
- The CRLF preceding each boundary line is consumed and not included in the preceding part's body, per RFC 2046 section 5.1.1.
- Header names are lowercased for case-insensitive access. So `Content-Type` becomes `content-type` in the returned dict.
- A `ValueError` is raised if the closing boundary (`--BOUNDARY--`) is missing.
- Preamble text before the first boundary and epilogue text after the closing boundary are ignored, as the RFC allows.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.


## License

MIT
