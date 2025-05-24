from abc import ABC, abstractmethod
from typing import Optional, Set

from src.entities.customer import Customer


class PriorityQueue(ABC):
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

    def print_queue(self):
        """
        Print the contents of the queue.
        """
        pass
