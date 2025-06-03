"""
Defines the Customer class, which represents a customer in the health clinic.
"""

from datetime import datetime


class Customer:
    def __init__(self, customer_id: int, arrival_time: datetime, ticket_type: str):
        self.customer_id = customer_id
        self.arrival_time = arrival_time
        self.ticket_type = ticket_type
        self.jumps = 0

    def __eq__(self, other):
        return self.customer_id == other.customer_id

    def __lt__(self, other):
        return self.customer_id < other.customer_id

    def update_jumps(self) -> None:
        """Update the number of jumps this customer has made in the queue."""
        self.jumps += 1
