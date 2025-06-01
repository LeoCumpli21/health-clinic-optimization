"""
Defines the ServiceWindow class, which represents a service window in the health clinic.
"""

from datetime import datetime
from typing import Optional
from src.entities.customer import Customer


class ServiceWindow:
    """Represents a service window in the clinic."""

    def __init__(self, window_id: int):
        self.window_id = window_id
        self.is_available = True
        self.current_customer: Optional[Customer] = None
        self.service_end_time: Optional[datetime] = None

    def start_service(self, customer: Customer, service_end_time: datetime) -> None:
        """Start serving a customer at this window."""
        self.is_available = False
        self.current_customer = customer
        self.service_end_time = service_end_time

    def finish_service(self) -> Optional[Customer]:
        """Finish serving the current customer and make window available."""
        if self.current_customer is None:
            return None

        finished_customer = self.current_customer
        self.is_available = True
        self.current_customer = None
        self.service_end_time = None
        return finished_customer

    def is_service_complete(self, current_time: datetime) -> bool:
        """Check if current service is complete."""
        if self.service_end_time is None:
            return False
        return current_time >= self.service_end_time
