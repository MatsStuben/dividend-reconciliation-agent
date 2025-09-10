from anthropic import Anthropic
import os

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_classification(payload: dict, model="claude-sonnet-4-20250514", max_tokens=600) -> str:

    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=payload["system"],
        messages=payload["messages"]
    )

    for block in resp.content:
        if block.type == "text":
            return block.text

    return "" 