from abc import ABC, abstractmethod


class PriorityQueue(ABC):
    @abstractmethod
    def enqueue(self, item, priority):
        """
        Add an item to the queue with a given priority.
        :param item: The item to add to the queue.
        :param priority: The priority of the item.
        """
        pass

    @abstractmethod
    def dequeue(self):
        """
        Remove and return the item with the highest priority from the queue.
        :return: The item with the highest priority.
        """
        pass

    @abstractmethod
    def update_priority(self, item, new_priority):
        """
        Update the priority of an item in the queue.
        :param item: The item whose priority to update.
        :param new_priority: The new priority of the item.
        """
        pass

    def print_queue(self):
        """
        Print the contents of the queue.
        """
        pass
