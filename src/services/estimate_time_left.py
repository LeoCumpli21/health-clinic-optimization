"""This module provides functions to estimate service times for customers in a queue."""

from datetime import datetime
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


def estimate_total_times_in_line(
    service_points: int,
    queue: PriorityQueue,
    service_times_repo: Repository,
    current_time: datetime,  # Add current_time parameter
) -> List[Tuple[Customer, float]]:
    """Estimates the total waiting time for every customer in the queue.

    The total waiting time is the sum of the time already spent in the queue
    and the estimated time remaining until they are served.

    Args:
        service_points (int): The number of service points available.
        queue (PriorityQueue): The queue object.
        service_times_repo (Repository): The repository object to fetch service times.
        current_time (datetime): The current time, used to calculate how long
            a customer has already been waiting.

    Returns:
        List[Tuple[Customer, float]]: A list of tuples, where each tuple contains
            a customer and their total estimated waiting time in minutes (sum of
            time already waited and estimated future wait time in the queue).
    """
    time_left = 0
    output = []
    for customer in queue:
        # Get the estimated service time given the ticket type
        service_time = get_estimated_service_time(customer, service_times_repo)

        # This is the estimated time left in the queue before being served
        estimated_time_left_in_queue = time_left / service_points

        # Calculate the time the customer has already waited in minutes
        time_already_waited = (
            current_time - customer.arrival_time
        ).total_seconds() / 60.0

        # Total estimated time is the sum of time already waited and time left
        total_estimated_time = time_already_waited + estimated_time_left_in_queue

        output.append((customer, total_estimated_time))

        # Add current customer's service time to the time_left for the next customer
        time_left += service_time

    return output
