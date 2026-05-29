import json
import unittest

from app.services.ai.dataset_qa import build_tool_followup_messages


class DatasetQAToolFollowupTests(unittest.TestCase):
    def test_builds_openai_compatible_tool_followup_messages(self) -> None:
        context = {
            "summary": {"row_count": 3},
            "columns": [{"name": "revenue", "data_type": "integer"}],
        }
        tool_calls = [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "describe_dataset_context",
                    "arguments": json.dumps({"focus": "summary"}),
                },
            }
        ]

        messages = build_tool_followup_messages(context=context, tool_calls=tool_calls)

        self.assertEqual(messages[0]["role"], "assistant")
        self.assertEqual(messages[0]["tool_calls"], tool_calls)
        self.assertEqual(messages[1]["role"], "tool")
        self.assertEqual(messages[1]["tool_call_id"], "call_123")
        self.assertEqual(messages[1]["name"], "describe_dataset_context")
        tool_content = json.loads(messages[1]["content"])
        self.assertEqual(tool_content["focus"], "summary")
        self.assertEqual(tool_content["result"], {"row_count": 3})


if __name__ == "__main__":
    unittest.main()
