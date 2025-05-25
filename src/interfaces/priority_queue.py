from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.entities.customer import Customer


class PriorityQueue(ABC):
    def __init__(self, queue: Sequence[Customer]):
        """Initialize the priority queue.

        Args:
            queue (Sequence[Customer]): The initial sequence of customers.
        """
        self.queue = queue
        pass

    def __iter__(self):
        """Iterate over the customers in the queue.

        Returns:
            An iterator over the customers in the queue.
        """
        return iter(self.queue)

    def __len__(self) -> int:
        """Get the number of customers in the queue.

        Returns:
            int: The number of customers in the queue.
        """
        return len(self.queue)

    def __getitem__(self, index: int) -> Customer:
        """Get a customer at a specific index in the queue.

        Args:
            index (int): The index of the customer to retrieve.

        Returns:
            Customer: The customer at the specified index.
        """
        return self.queue[index]

    @abstractmethod
    def enqueue(self, customer: Customer) -> None:
        """Add a customer to the queue.

        Args:
            customer (Customer): The customer to add to the queue.
        """
        pass

    @abstractmethod
    def dequeue(self) -> Optional[Customer]:
        """Remove and return the customer with the highest priority from the queue.

        Returns:
            Optional[Customer]: The customer with the highest priority, or None if the queue is empty.
        """
        pass

    @abstractmethod
    def update_priority(self, customer: Customer, new_position: int) -> None:
        """Update the position of a customer in the queue.

        Args:
            customer (Customer): The customer object whose position is to be updated.
            new_position (int): The new index (0-based) where the customer
                                should be placed in the queue.
        """
        pass

    @abstractmethod
    def print_queue(self) -> None:
        """Print the contents of the queue."""
        pass
