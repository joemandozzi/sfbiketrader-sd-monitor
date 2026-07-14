import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from sfmonitor.extract import FrameMention, extract_frame_info


def _mock_client(response_text: str) -> MagicMock:
    client = MagicMock()
    client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=response_text)]
    )
    return client


class TestExtractFrameInfo(unittest.TestCase):
    def test_empty_caption_skips_api_call(self):
        client = _mock_client("[]")
        result = extract_frame_info("   ", client=client)
        self.assertEqual(result, [])
        client.messages.create.assert_not_called()

    def test_single_frame(self):
        payload = [
            {
                "brand": "Bianchi",
                "model": "Volpe",
                "frame_size": "58cm",
                "price": "$400",
                "condition": "used",
            }
        ]
        client = _mock_client(json.dumps(payload))
        result = extract_frame_info("58cm Bianchi Volpe, $400 obo", client=client)
        self.assertEqual(
            result,
            [FrameMention(brand="Bianchi", model="Volpe", frame_size="58cm", price="$400", condition="used")],
        )

    def test_multiple_frames(self):
        payload = [
            {"brand": "Trek", "model": "520", "frame_size": None, "price": None, "condition": None},
            {"brand": "Surly", "model": "Cross-Check", "frame_size": "56", "price": "$300", "condition": "good"},
        ]
        client = _mock_client(json.dumps(payload))
        result = extract_frame_info("Trek 520 and a Surly Cross-Check 56 $300", client=client)
        self.assertEqual(len(result), 2)

    def test_no_frame_mentioned(self):
        client = _mock_client("[]")
        result = extract_frame_info("just a group ride photo, no bikes for sale", client=client)
        self.assertEqual(result, [])

    def test_strips_markdown_code_fence(self):
        payload = [{"brand": "Ross", "model": "Mt Hood", "frame_size": None, "price": "$400", "condition": None}]
        fenced = "```json\n" + json.dumps(payload) + "\n```"
        client = _mock_client(fenced)
        result = extract_frame_info("Ross mt hood for sale $400", client=client)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].brand, "Ross")

    def test_malformed_json_returns_empty(self):
        client = _mock_client("not valid json")
        result = extract_frame_info("some caption", client=client)
        self.assertEqual(result, [])

    def test_skips_leading_thinking_block(self):
        payload = [{"brand": "Trek", "model": "520", "frame_size": None, "price": None, "condition": None}]
        client = MagicMock()
        client.messages.create.return_value = SimpleNamespace(
            content=[
                SimpleNamespace(type="thinking", thinking="reasoning about the caption..."),
                SimpleNamespace(type="text", text=json.dumps(payload)),
            ]
        )
        result = extract_frame_info("Trek 520 for sale", client=client)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].brand, "Trek")

    def test_no_text_block_returns_empty(self):
        client = MagicMock()
        client.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(type="thinking", thinking="reasoning only, no text block")]
        )
        result = extract_frame_info("some caption", client=client)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
