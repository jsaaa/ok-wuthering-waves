import io
import json
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


class DiscordWebhookNotifier:
    def __init__(self, webhook_url: str, username: str = "", timeout: int = 15):
        self.webhook_url = webhook_url.strip()
        self.username = username.strip()
        self.timeout = timeout

    def send(
        self,
        title: str,
        message: str,
        level: str,
        task_name: str = "",
        screenshot=None,
        mention_user_id: str = "",
    ) -> None:
        if not self.webhook_url:
            return

        content = self._build_message(title, message, level, task_name, mention_user_id)
        image_bytes = self._image_to_bytes(screenshot) if screenshot is not None else None
        payload = self._build_payload(content, image_bytes is not None)
        if self.username:
            payload["username"] = self.username

        import requests

        if image_bytes is None:
            response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
        else:
            response = requests.post(
                self._enable_components(self.webhook_url),
                data={"payload_json": json.dumps(payload, ensure_ascii=False)},
                files={"files[0]": ("screenshot.jpg", image_bytes, "image/jpeg")},
                timeout=self.timeout,
            )

        response.raise_for_status()

    @staticmethod
    def _build_message(
        title: str,
        message: str,
        level: str,
        task_name: str,
        mention_user_id: str,
    ) -> str:
        lines = []
        mention_user_id = mention_user_id.strip()
        if mention_user_id:
            lines.append(f"<@{mention_user_id}>")
        lines.append(f"**{title}**")
        lines.append(str(message))
        footer = [f"Level: {level}", f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        if task_name:
            footer.insert(0, f"Task: {task_name}")
        lines.append("")
        lines.append("-# " + " | ".join(footer))
        return "\n".join(lines)

    @staticmethod
    def _build_payload(content: str, has_screenshot: bool) -> dict:
        if not has_screenshot:
            return {"content": content}

        return {
            "flags": 1 << 15,
            "attachments": [{"id": 0, "filename": "screenshot.jpg"}],
            "components": [
                {
                    "type": 17,
                    "components": [
                        {
                            "type": 9,
                            "components": [{"type": 10, "content": content}],
                            "accessory": {
                                "type": 11,
                                "media": {"url": "attachment://screenshot.jpg"},
                                "description": "Screenshot",
                            },
                        }
                    ],
                }
            ],
        }

    @staticmethod
    def _enable_components(url: str) -> str:
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["with_components"] = "true"
        return urlunparse(parsed._replace(query=urlencode(query)))

    @staticmethod
    def _image_to_bytes(image):
        import cv2

        success, encoded = cv2.imencode(".jpg", image)
        if not success:
            return None
        return io.BytesIO(encoded.tobytes())
