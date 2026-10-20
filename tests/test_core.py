import unittest

from simple_mime_multipart import parse_multipart


class TestParseMultipart(unittest.TestCase):

    def test_single_part(self):
        body = (
            "--BOUNDARY\r\n"
            "Content-Type: text/plain\r\n"
            "\r\n"
            "Hello, world!\r\n"
            "--BOUNDARY--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "BOUNDARY")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["headers"]["content-type"], "text/plain")
        self.assertEqual(parts[0]["body"], b"Hello, world!")

    def test_multiple_parts(self):
        body = (
            "--BOUNDARY\r\n"
            "Content-Type: text/plain\r\n"
            "\r\n"
            "First\r\n"
            "--BOUNDARY\r\n"
            "Content-Type: text/html\r\n"
            "\r\n"
            "<p>Second</p>\r\n"
            "--BOUNDARY--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "BOUNDARY")
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0]["body"], b"First")
        self.assertEqual(parts[1]["body"], b"<p>Second</p>")
        self.assertEqual(parts[1]["headers"]["content-type"], "text/html")

    def test_case_insensitive_headers(self):
        body = (
            "--B\r\n"
            "Content-Type: text/plain\r\n"
            "\r\n"
            "data\r\n"
            "--B--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(parts[0]["headers"]["content-type"], "text/plain")
        self.assertEqual(parts[0]["headers"]["CONTENT-TYPE"], "text/plain")

    def test_header_value_stripped(self):
        body = (
            "--B\r\n"
            "Content-Type:    text/plain   \r\n"
            "\r\n"
            "data\r\n"
            "--B--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(parts[0]["headers"]["content-type"], "text/plain")

    def test_part_with_no_headers(self):
        body = (
            "--B\r\n"
            "\r\n"
            "just a body\r\n"
            "--B--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["headers"], {})
        self.assertEqual(parts[0]["body"], b"just a body")

    def test_body_with_blank_lines(self):
        body = (
            "--B\r\n"
            "Content-Type: text/plain\r\n"
            "\r\n"
            "Line one\r\n"
            "\r\n"
            "Line three\r\n"
            "--B--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(parts[0]["body"], b"Line one\r\n\r\nLine three")

    def test_body_containing_boundary_like_text(self):
        """A line that merely contains the boundary as a substring must not split."""
        body = (
            "--B\r\n"
            "\r\n"
            "This --B is not a delimiter\r\n"
            "--B--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["body"], b"This --B is not a delimiter")

    def test_body_with_trailing_crlf_before_boundary(self):
        body = (
            "--B\r\n"
            "\r\n"
            "content\r\n"
            "--B--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(parts[0]["body"], b"content")

    def test_empty_body_part(self):
        body = (
            "--B\r\n"
            "Content-Type: text/plain\r\n"
            "\r\n"
            "--B--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(parts[0]["body"], b"")

    def test_missing_closing_boundary_raises(self):
        body = (
            "--B\r\n"
            "\r\n"
            "data\r\n"
        ).encode("utf-8")
        with self.assertRaises(ValueError):
            parse_multipart(body, "B")

    def test_empty_boundary_raises(self):
        with self.assertRaises(ValueError):
            parse_multipart(b"--x\r\n", "")

    def test_preamble_before_first_boundary_ignored(self):
        body = (
            "This is the preamble.\r\n"
            "It is ignored.\r\n"
            "--B\r\n"
            "\r\n"
            "actual content\r\n"
            "--B--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["body"], b"actual content")

    def test_epilogue_after_closing_boundary_ignored(self):
        body = (
            "--B\r\n"
            "\r\n"
            "content\r\n"
            "--B--\r\n"
            "This is the epilogue.\r\n"
            "Ignored.\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["body"], b"content")

    def test_multiple_headers_in_part(self):
        body = (
            "--B\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Disposition: form-data; name=\"field\"\r\n"
            "\r\n"
            "value\r\n"
            "--B--\r\n"
        ).encode("utf-8")
        parts = parse_multipart(body, "B")
        self.assertEqual(parts[0]["headers"]["content-type"], "text/plain")
        self.assertEqual(
            parts[0]["headers"]["content-disposition"],
            'form-data; name="field"'
        )


if __name__ == "__main__":
    unittest.main()
