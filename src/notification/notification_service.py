from ok import Logger

from src.notification.discord_webhook import DiscordWebhookNotifier

logger = Logger.get_logger(__name__)


class NotificationService:
    def __init__(self, config: dict | None):
        self.config = config or {}

    def notify(self, level: str, message: str, task=None) -> None:
        if not self.config.get("Enable Discord Webhook"):
            return
        if level == "INFO" and not self.config.get("Notify On Info", True):
            return
        if level == "ERROR" and not self.config.get("Notify On Error", True):
            return

        webhook_url = self.config.get("Discord Webhook URL", "")
        if not webhook_url:
            return

        screenshot = None
        if self.config.get("Attach Screenshot", True) and task is not None:
            screenshot = getattr(task, "frame", None)

        task_name = getattr(task, "name", "") or task.__class__.__name__ if task is not None else ""
        try:
            DiscordWebhookNotifier(
                webhook_url=webhook_url,
                username=self.config.get("Discord Username", ""),
            ).send(
                title="OK-WW",
                message=message,
                level=level,
                task_name=task_name,
                screenshot=screenshot,
                mention_user_id=self.config.get("Mention User ID", ""),
            )
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
