"""This module provides an implementation of a priority queue using collections.deque."""

from collections import deque
from datetime import datetime
from typing import Optional, List

from src.entities.customer import Customer
from src.interfaces.priority_queue import PriorityQueue


class PriorityQueueLeo(PriorityQueue):
    """
    A priority queue implementation using a deque from collections.
    """

    def __init__(self, queue: deque[Customer] | List[Customer]):
        """Initializes the priority queue with an optional deque or list.

        Args:
            queue (deque[Customer] | List[Customer]): An optional deque or list
                of Customer objects to initialize the queue. If a list is provided,
                it will be converted to a deque.
        """
        if isinstance(queue, list):
            queue = deque(queue)
        self.queue = queue

    def enqueue(self, customer: Customer) -> None:
        """Add a customer to the queue.

        Specifically, this implementation adds the customer to the rear (right end)
        of an internal deque.

        Args:
            customer (Customer): The customer object to be added.
        """
        self.queue.append(customer)
        return None

    def dequeue(self) -> Optional[Customer]:
        """Remove and return a customer from the queue.

        Specifically, this implementation removes and returns the customer
        from the front (left end) of an internal deque. This results
        in FIFO (First-In, First-Out) behavior.

        Returns:
            Optional[Customer]: The customer removed from the queue,
                                or None if the queue is empty.
        """
        if not self.queue:
            return None
        customer = self.queue.popleft()
        return customer

    def update_priority(self, customer: Customer, new_position: int) -> None:
        """Update the position of a customer in the queue.

        This method changes the customer's effective priority by moving them
        to a new position within the deque. The customer is first removed
        from their current position and then inserted at the specified
        `new_position`.

        Args:
            customer (Customer): The customer object whose position is to be updated.
            new_position (int): The new index (0-based) where the customer
                                should be placed in the queue.
        """
        self.queue.remove(customer)
        self.queue.insert(new_position, customer)
        return None

    def print_queue(self, current_time: Optional[datetime] = None) -> None:
        """Print the contents of the queue.

        Customers are displayed in order of processing priority,
        from highest priority (next to be dequeued) to lowest priority.
        The customer at the right end of the internal deque is dequeued first.
        """
        if not self.queue:
            print("Queue is empty.")
            return

        print("Current Queue (Highest priority first - i.e., next to be dequeued):")
        # self.queue.pop() removes from the right, so the rightmost element is highest priority.
        # We iterate self.queue in reverse to print from highest to lowest priority.
        # enumerate provides a rank, starting from 1 for the highest priority customer.
        for rank, customer in enumerate(self.queue, 1):
            print(
                f"Rank: {rank}, Customer ID: {customer.customer_id}, Ticket Type: {customer.ticket_type}",
                end="",
            )
            if current_time:
                time_waited = (
                    current_time - customer.arrival_time
                ).total_seconds() / 60.0
                print(f", Time waited: {time_waited:.2f} minutes")
        return None
