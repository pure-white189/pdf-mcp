import base64
import json
import os
import subprocess

from anthropic import Anthropic
from utils import render_page_to_image


def _get_windows_username():
    try:
        result = subprocess.run(
            ["cmd.exe", "/c", "echo", "%USERNAME%"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return None


_win_user = _get_windows_username()
SETTINGS_PATH = f"/mnt/c/Users/{_win_user}/.claude/settings.json" if _win_user else None


def load_settings():
    if not SETTINGS_PATH:
        raise RuntimeError("Cannot detect Windows username to locate settings.json")
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Settings file not found: {SETTINGS_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in settings file: {e}")


def bytes_to_base64_str(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("输入必须是 bytes 或 bytearray 类型")

    # base64.b64encode 返回 bytes，需要再解码成 str
    encoded_bytes = base64.b64encode(data)
    return encoded_bytes.decode("utf-8")


def extract_text_from_image(data):
    settings = load_settings()
    env = settings["env"]
    try:
        client = Anthropic(
            base_url=env["ANTHROPIC_BASE_URL"],
            auth_token=env["ANTHROPIC_AUTH_TOKEN"],
            timeout=60.0,
        )
    except KeyError as e:
        raise ValueError(f"Missing config key in settings.json: {e}")

    try:
        response = client.messages.create(
            model=env.get("ANTHROPIC_VISION_MODEL", env["ANTHROPIC_DEFAULT_HAIKU_MODEL"]),
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "请提取这个页面的所有文字内容"
                        }
                    ],
                }
            ],
        )
    except Exception as e:
        raise RuntimeError(f"Anthropic API call failed: {e}") from e

    # API may return ThinkingBlock + TextBlock; find the text block
    for block in response.content:
        if block.type == "text":
            return block.text
    raise RuntimeError("API returned no text block in response")


def extract_text_from_page(pdf_path, page_number):
    image_bytes = render_page_to_image(pdf_path, page_number)
    base64_str = bytes_to_base64_str(image_bytes)
    return extract_text_from_image(base64_str)
