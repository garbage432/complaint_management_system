import io
import json
import os
from unittest.mock import patch
from urllib.error import HTTPError

from django.test import TestCase


class ChatbotFallbackTests(TestCase):
    def test_chatbot_uses_clean_reply_when_groq_is_forbidden(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "dummy-key"}, clear=False):
            with patch("urllib.request.urlopen") as mocked_urlopen:
                mocked_urlopen.side_effect = HTTPError(
                    url="https://api.groq.com/openai/v1/chat/completions",
                    code=403,
                    msg="Forbidden",
                    hdrs=None,
                    fp=io.BytesIO(b'{"error": {"message": "Forbidden"}}'),
                )

                response = self.client.post(
                    "/chatbot/",
                    data=json.dumps({"message": "what departments are available?"}),
                    content_type="application/json",
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("Available departments include", payload["reply"])
        self.assertNotIn("[Fallback]", payload["reply"])
        self.assertNotIn("HTTP Error 403", payload["reply"])
