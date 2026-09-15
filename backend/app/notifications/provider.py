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
        for provider in self.providers:
            result = await provider.send_alert(event, recipient_ids=recipient_ids)
            results.append(result)
        return results
