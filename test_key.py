import os
from anthropic import Anthropic

key = os.environ.get("ANTHROPIC_API_KEY", "")

if not key:
    print("NO KEY FOUND in ANTHROPIC_API_KEY environment variable.")
else:
    print(f"Found key: {key[:12]}...{key[-4:]}  (length {len(key)})")

    client = Anthropic(api_key=key)
    try:
        resp = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}],
        )
        print("SUCCESS:", resp.content[0].text)
    except Exception as e:
        print("FAILED:", e)