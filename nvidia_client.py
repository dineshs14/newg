"""
Blast Radius Agent — NVIDIA API Client
========================================
Wraps the NVIDIA Nemotron streaming API with thinking/reasoning support.
Uses the OpenAI SDK with a custom base_url.
"""

import sys
import time
import threading
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError

from config import (
    NVIDIA_BASE_URL,
    NVIDIA_API_KEY,
    MODEL_NAME,
    TEMPERATURE,
    TOP_P,
    MAX_TOKENS,
    REASONING_BUDGET,
)


# ── Spinner for visual feedback while streaming ─────────────────────────────

class Spinner:
    """Animated spinner that runs in a background thread."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Analyzing"):
        self.message = message
        self._stop_event = threading.Event()
        self._thread = None

    def _spin(self):
        idx = 0
        while not self._stop_event.is_set():
            frame = self.FRAMES[idx % len(self.FRAMES)]
            sys.stderr.write(f"\r  {frame} {self.message}...")
            sys.stderr.flush()
            idx += 1
            time.sleep(0.1)
        sys.stderr.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stderr.flush()

    def start(self):
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()


# ── NVIDIA API Call ──────────────────────────────────────────────────────────

def call_nvidia(prompt: str, show_thinking: bool = False) -> str:
    """
    Send a prompt to the NVIDIA Nemotron API with streaming and
    chain-of-thought (reasoning) support.

    Args:
        prompt: The fully assembled prompt string.
        show_thinking: If True, print the model's internal reasoning trace.

    Returns:
        The model's final answer as a string.

    Raises:
        SystemExit: On fatal API errors (missing key, connection failure).
    """

    if not NVIDIA_API_KEY:
        print("\n╔═══════════════════════════════════════════════════════════╗")
        print("║  ERROR: NVIDIA_API_KEY is not set.                       ║")
        print("║                                                           ║")
        print("║  Set it via environment variable:                         ║")
        print("║    export NVIDIA_API_KEY=nvapi-XXXXXXXXXXXXXXXX           ║")
        print("║                                                           ║")
        print("║  Or create a .env file in the project root:               ║")
        print("║    NVIDIA_API_KEY=nvapi-XXXXXXXXXXXXXXXX                  ║")
        print("║                                                           ║")
        print("║  Get your free key at:                                    ║")
        print("║    https://build.nvidia.com/                              ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        sys.exit(1)

    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)

    spinner = Spinner("Sending to NVIDIA Nemotron API")
    spinner.start()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_TOKENS,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": True},
            },
            stream=True,
        )
    except APIConnectionError:
        spinner.stop()
        print("\n✖ Connection Error: Could not reach the NVIDIA API.")
        print("  → Check your internet connection.")
        print("  → Verify the API URL: " + NVIDIA_BASE_URL)
        sys.exit(1)
    except RateLimitError:
        spinner.stop()
        print("\n✖ Rate Limit: You've exceeded the free tier quota.")
        print("  → Wait a few minutes and try again.")
        print("  → Check your usage at https://build.nvidia.com/")
        sys.exit(1)
    except APIStatusError as e:
        spinner.stop()
        print(f"\n✖ API Error ({e.status_code}): {e.message}")
        if e.status_code == 401:
            print("  → Your API key may be invalid or expired.")
        elif e.status_code == 404:
            print(f"  → Model '{MODEL_NAME}' may not be available.")
        sys.exit(1)

    # ── Stream and collect response ──────────────────────────────────────

    reasoning_parts: list[str] = []
    answer_parts: list[str] = []
    first_content = True

    try:
        for chunk in completion:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Capture reasoning/thinking content
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                reasoning_parts.append(reasoning)

            # Capture final answer content
            if delta.content:
                if first_content:
                    spinner.stop()
                    first_content = False
                answer_parts.append(delta.content)

    except Exception as e:
        spinner.stop()
        print(f"\n✖ Streaming Error: {e}")
        print("  → The API connection may have dropped.")
        print("  → Try running the command again.")
        sys.exit(1)

    spinner.stop()

    # ── Display reasoning trace if requested ─────────────────────────────

    if show_thinking and reasoning_parts:
        reasoning_text = "".join(reasoning_parts)
        print()
        print("┌─── 🧠 MODEL REASONING TRACE ────────────────────────────┐")
        for line in reasoning_text.splitlines():
            print(f"│ {line}")
        print("└──────────────────────────────────────────────────────────┘")
        print()

    answer = "".join(answer_parts)

    if not answer.strip():
        print("\n⚠ Warning: The model returned an empty response.")
        print("  → The input may have been too large for the token limit.")
        print("  → Try reducing the size of your input files.")
        return ""

    return answer
