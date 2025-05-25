"""This module provides functions to estimate service times for customers in a queue."""

from typing import List, Tuple

from src.entities.customer import Customer
from src.interfaces.priority_queue import PriorityQueue
from src.interfaces.repository import Repository


def get_estimated_service_time(
    customer: Customer, service_times_repo: Repository
) -> float:
    """Gets the estimated service time for a customer based on their ticket type.

    Args:
        customer (Customer): The customer object.
        service_times_repo (Repository): The repository object to fetch service times.

    Returns:
        float: The estimated service time for the customer.
    """
    # Get the estimated service time given the ticket type
    return service_times_repo.get_data({"ticket_type": customer.ticket_type}).iloc[0][
        "service_time"
    ]


def estimate_times_left(
    service_points: int, queue: PriorityQueue, service_times_repo: Repository
) -> List[Tuple[Customer, float]]:
    """Estimates the time left for every customer in the queue.

    Args:
        service_points (int): The number of service points available.
        queue (PriorityQueue): The queue object.
        service_times_repo (Repository): The repository object to fetch service times.

    Returns:
        List[Tuple[Customer, float]]: A list of tuples, where each tuple contains
            a customer and their estimated time left in the queue.
    """
    time_left = 0
    output = []
    for customer in queue:
        # Get the estimated service time given the ticket type
        service_time = service_times_repo.get_data(
            {"ticket_type": customer.ticket_type}
        ).iloc[0]["service_time"]
        # Add the service time to the total time left
        time_left += service_time
        output.append((customer, time_left / service_points))

    return output
