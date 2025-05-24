from abc import ABC, abstractmethod
from typing import Any, Optional, Set, Iterable

from src.entities.customer import Customer


class PriorityQueue(ABC):
    def __init__(self, queue: Iterable[Any]):
        """
        Initialize the priority queue.

        """
        self.queue = queue
        pass

    def __iter__(self):
        """
        Iterate over the customers in the queue.
        :return: An iterator over the customers in the queue.
        """
        return iter(self.queue)

    @abstractmethod
    def enqueue(self, customer, priority):
        """
        Add a customer to the queue with a given priority.
        :param customer: The customer to add to the queue.
        :param priority: The priority of the customer.
        """
        pass

    @abstractmethod
    def dequeue(self) -> Optional[Customer]:
        """
        Remove and return the customer with the highest priority from the queue.
        :return: The customer with the highest priority.
        """
        pass

    @abstractmethod
    def update_priority(
        self, customer_id: int, new_priority: int, priority_ticket_types: Set[str]
    ):
        """
        Update the priority of a customer in the queue.
        :param customer_id: The ID of the customer whose priority to update.
        :param new_priority: The new priority of the customer.
        :param priority_ticket_types: A set of ticket types that are considered priority.
        """
        pass

    @abstractmethod
    def print_queue(self):
        """
        Print the contents of the queue.
        """
        pass
