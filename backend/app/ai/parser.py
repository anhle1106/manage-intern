import json
import re
from app.ai.schemas import TopicExtraction


def parse_ai_response(text: str) -> TopicExtraction:
    cleaned = text.strip()

    json_match = re.search(r'```(?:json)?\s*(.*?)```', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(1).strip()

    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        if start != -1:
            cleaned = cleaned[start:]

    if not cleaned.endswith("}"):
        end = cleaned.rfind("}")
        if end != -1:
            cleaned = cleaned[:end + 1]

    data = json.loads(cleaned)
    return TopicExtraction(**data)
