import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, call, patch
from urllib.error import HTTPError, URLError

import update_all as updater


class DownloadRetryTests(unittest.TestCase):
    def response(self, content=b'{"matches": []}'):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = content
        return response

    def error(self, code):
        return HTTPError("https://example.test", code, "failure", {}, io.BytesIO())

    @patch.object(updater.time, "sleep")
    @patch.object(updater.urllib.request, "urlopen")
    def test_502_then_success(self, urlopen, sleep):
        urlopen.side_effect = [self.error(502), self.response()]
        output = io.StringIO()
        with redirect_stdout(output):
            result = updater.download("https://example.test", "matches.json",
                                      {"X-Auth-Token": "test-secret"})
        self.assertEqual(result, b'{"matches": []}')
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(5)
        self.assertNotIn("test-secret", output.getvalue())
        for args in urlopen.call_args_list:
            self.assertEqual(args.args[0].get_header("X-auth-token"), "test-secret")
            self.assertEqual(args.kwargs["timeout"], 30)

    @patch.object(updater.time, "sleep")
    @patch.object(updater.urllib.request, "urlopen")
    def test_persistent_server_failure_is_bounded(self, urlopen, sleep):
        for code in (500, 502, 503, 504):
            with self.subTest(code=code):
                urlopen.reset_mock()
                sleep.reset_mock()
                urlopen.side_effect = [self.error(code) for _ in range(3)]
                with self.assertRaises(HTTPError):
                    updater.download("https://example.test", "matches.json")
                self.assertEqual(urlopen.call_count, 3)
                self.assertEqual(sleep.call_args_list, [call(5), call(10)])

    @patch.object(updater.time, "sleep")
    @patch.object(updater.urllib.request, "urlopen")
    def test_permanent_http_errors_not_retried(self, urlopen, sleep):
        for code in (400, 401, 403, 404):
            with self.subTest(code=code):
                urlopen.reset_mock()
                urlopen.side_effect = self.error(code)
                with self.assertRaises(HTTPError):
                    updater.download("https://example.test", "matches.json")
                self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()

    @patch.object(updater.time, "sleep")
    @patch.object(updater.urllib.request, "urlopen")
    def test_network_errors_and_timeouts_retried(self, urlopen, sleep):
        urlopen.side_effect = [URLError("temporary"), TimeoutError(), self.response()]
        self.assertEqual(updater.download("https://example.test", "matches.json"),
                         b'{"matches": []}')
        self.assertEqual(sleep.call_args_list, [call(5), call(10)])

    @patch.object(updater.time, "sleep")
    @patch.object(updater.urllib.request, "urlopen")
    def test_success_does_not_sleep(self, urlopen, sleep):
        urlopen.return_value = self.response(b"BEGIN:VCALENDAR\nEND:VCALENDAR")
        self.assertTrue(updater.download("https://example.test", "source.ics"))
        urlopen.assert_called_once()
        sleep.assert_not_called()

    @patch.object(updater.time, "sleep")
    @patch.object(updater.urllib.request, "urlopen")
    def test_failed_download_preserves_existing_json(self, urlopen, sleep):
        urlopen.side_effect = [self.error(502) for _ in range(3)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matches.json"
            path.write_text('{"matches": [{"id": 123}]}')
            original = path.read_bytes()
            with patch.object(updater, "BASE_DIR", Path(directory)), \
                    patch.object(updater, "FOOTBALL_DATA_TOKEN", "test-secret"):
                with self.assertRaises(HTTPError):
                    updater.download_football_data("https://example.test", path.name)
            self.assertEqual(path.read_bytes(), original)

    @patch.object(updater.time, "sleep")
    @patch.object(updater.urllib.request, "urlopen")
    def test_empty_response_still_fails(self, urlopen, sleep):
        urlopen.return_value = self.response(b"")
        with self.assertRaisesRegex(RuntimeError, "Réponse vide"):
            updater.download("https://example.test", "source.ics")
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
