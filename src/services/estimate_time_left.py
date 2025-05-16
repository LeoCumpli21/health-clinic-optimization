from src.interfaces.priority_queue import PriorityQueue
from src.interfaces.repository import Repository


def estimate_time_left(
    customer_id, service_points, queue: PriorityQueue, service_times_repo: Repository
) -> float:
    """
    Estimate the time left for a customer in the queue.
    :param customer_id: The id of the customer in the queue.
    :param service_points: The number of service points available.
    :param queue: The queue object.
    :param service_times_repo: The repository object to fetch service times.
    :return: The estimated time left for the customer in the queue.
    """
    time_left = 0
    for customer in queue:
        if customer.customer_id == customer_id:
            return time_left / service_points
        else:
            # Get the estimated service time given the ticket type
            service_time = service_times_repo.get_data(
                {"ticket_type": customer.ticket_type}
            ).iloc[0]["service_time"]
            # Add the service time to the total time left
            time_left += service_time

    return 0
