from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.alert import AlertEvent, NotificationResult


class NotificationProvider(ABC):
    @abstractmethod
    async def send_alert(
        self,
        event: AlertEvent,
        recipient_ids: Optional[List[str]] = None,
    ) -> NotificationResult:
        """
        Send a notification for the given alert event.

        Args:
            event: The alert event to notify about.
            recipient_ids: Override the global recipient list for this specific send.
                           If None or empty, fall back to the provider's configured recipients.
        """
        ...


class NotificationService:
    """Dispatches notifications through all registered providers."""

    def __init__(self, providers: List[NotificationProvider]):
        self.providers = providers

    async def notify_all(
        self,
        event: AlertEvent,
        recipient_ids: Optional[List[str]] = None,
    ) -> List[NotificationResult]:
        results = []
        import logging
        log = logging.getLogger("notification_service")
        for provider in self.providers:
            try:
                result = await provider.send_alert(event, recipient_ids=recipient_ids)
                results.append(result)
            except Exception as e:
                log.error("Provider %s failed to send alert: %s", provider.__class__.__name__, e, exc_info=True)
                results.append(NotificationResult(success=False, error_message=str(e)))
        return results
