import heapq
from typing import Set, Tuple

from src.entities.customer import Customer
from src.interfaces.priority_queue import PriorityQueue


class PriorityQueueLeo(PriorityQueue):
    """
    A priority queue implementation using a heap. Items are stored as tuples of (priority, Customer).
    """

    def __init__(self, heap: list[Tuple[int, Customer]] = []):
        """
        Initialize the priority queue with an optional heap.

        Args:
            heap (list[Tuple[int, Customer]]): A list of (priority, Customer) tuples to initialize the heap.
        """
        self.heap = heap
        heapq.heapify(self.heap)

    def enqueue(self, customer: Customer, priority: int):
        """
        Add a customer to the priority queue with a given priority.

        Args:
            customer (Customer): The customer to add to the queue.
            priority (int): The priority of the customer.
        """
        heapq.heappush(self.heap, (priority, customer))
        return None

    def dequeue(self):
        """
        Remove and return the customer with the highest priority (lowest priority value).

        Returns:
            Customer: The customer with the highest priority, or None if the queue is empty.
        """
        if not self.heap:
            return None
        _, customer = heapq.heappop(self.heap)
        # Decrease all remaining customers' priorities by 1
        updated_heap = [(p - 1, c) for p, c in self.heap]
        heapq.heapify(updated_heap)
        self.heap = updated_heap
        return customer

    def update_priority(
        self, customer_id: int, new_priority: int, priority_ticket_types: Set[str]
    ):
        """
        Update the priority of a specific customer and adjust priorities of others if necessary.

        Args:
            customer_id (int): The ID of the customer whose priority needs to be updated.
            new_priority (int): The new priority value for the customer.
            priority_ticket_types (Set[str]): A set of ticket types that should have adjusted priorities.
        """
        updated_heap = []
        for priority, current_customer in self.heap:
            if current_customer.customer_id == customer_id:
                # Update the priority of the specified customer
                updated_heap.append((new_priority, current_customer))
            else:
                # Adjust priorities for customers with specific ticket types
                if (
                    current_customer.ticket_type in priority_ticket_types
                    and priority >= new_priority
                ):
                    updated_heap.append((priority + 1, current_customer))
                else:
                    updated_heap.append((priority, current_customer))
        heapq.heapify(updated_heap)
        self.heap = updated_heap
        return None

    def print_queue(self):
        """
        Print the contents of the priority queue in order of priority.
        """
        sorted_queue = sorted(self.heap, key=lambda x: x[0])
        for priority, customer in sorted_queue:
            print(
                f"Priority: {priority}, Customer ID: {customer.customer_id}, Ticket Type: {customer.ticket_type}"
            )
        return None
