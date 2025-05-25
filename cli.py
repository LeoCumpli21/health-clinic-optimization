from src.entities.customer import Customer
from typing import Set

from src.external_systems.priority_queue_leo import PriorityQueueLeo
from src.external_systems.dataframe_repo import DataFrameRepo
from src.interfaces.repository import Repository
from src.interfaces.priority_queue import PriorityQueue as PriorityQueueInterface
from src.services.manipulate_queue import update_queue_improved
from src.services.estimate_time_left import estimate_times_left

import pandas as pd


def prueba_1():
    # Create some example customers
    customer1 = Customer(customer_id=1, arrival_time=5, ticket_type="Regular")
    customer2 = Customer(customer_id=2, arrival_time=6, ticket_type="VIP")
    customer3 = Customer(customer_id=3, arrival_time=7, ticket_type="VIP")
    customer4 = Customer(customer_id=4, arrival_time=8, ticket_type="Regular")

    # Initialize the priority queue with an empty list
    priority_queue = PriorityQueueLeo([])

    # Enqueue customers
    priority_queue.enqueue(customer1)
    priority_queue.enqueue(customer2)
    priority_queue.enqueue(customer3)
    priority_queue.enqueue(customer4)

    priority_queue.print_queue()

    # Dequeue the customer
    # With appendleft and pop, the queue is FIFO.
    # Enqueue order: c1, c2, c3, c4. Deque: [c4, c3, c2, c1]
    # Dequeue order: c1, c2, c3, c4
    dequeued_customer = priority_queue.dequeue()
    if dequeued_customer:
        print(f"Dequeued customer: {dequeued_customer.customer_id}")  # Expected: 1

    priority_queue.print_queue()

    # Update the position of a specific customer
    # Current deque (after c1 dequeued): [c4, c3, c2]
    # To move customer4 (currently at the leftmost, last to be dequeued) to be dequeued next (rightmost)
    # new_position should be len(priority_queue.queue) - 1
    if customer4 in priority_queue.queue:
        priority_queue.update_priority(customer4, len(priority_queue.queue) - 1)
    print(f"After updating position of customer {customer4.customer_id}:")
    priority_queue.print_queue()

    # Dequeue again
    dequeued_customer = priority_queue.dequeue()
    if dequeued_customer:
        print(f"Dequeued customer: {dequeued_customer.customer_id}")  # Expected: 4

    priority_queue.print_queue()


def prueba_2():
    # Helper function to print queue details
    def print_queue_with_estimates(
        header: str,
        queue_to_print: PriorityQueueInterface,
        service_points_val: int,
        repo: Repository,
        current_time_val: float = 0.0,  # This parameter is kept for potential future use or clarity
    ):
        print(f"\n--- {header} ---")
        if len(queue_to_print) > 0:
            estimates = estimate_times_left(service_points_val, queue_to_print, repo)
            print(
                "Queue Order (ID, Type, Arrival): Estimated Time Left (until service completion)"
            )

            q_iterable = (
                queue_to_print.queue
                if hasattr(queue_to_print, "queue")
                else queue_to_print
            )

            for i, customer_obj in enumerate(q_iterable):
                # estimates contains (Customer, estimated_time_until_completion)
                # We need to find the estimate for the current customer_obj
                # Assuming estimates are in the same order as q_iterable
                est_time_left = estimates[i][1]
                print(
                    f"{i+1}. C{customer_obj.customer_id} ({customer_obj.ticket_type}, Arr@{customer_obj.arrival_time}): "
                    f"Est. Time Left={est_time_left:.2f}"
                )
        else:
            print("Queue is empty.")
        print("-" * (len(header) + 8))

        # 1. Create Customer objects

    customer1 = Customer(customer_id=1, arrival_time=0, ticket_type="Regular")
    customer2 = Customer(customer_id=2, arrival_time=1, ticket_type="VIP")
    customer3 = Customer(customer_id=3, arrival_time=2, ticket_type="Regular")
    customer4 = Customer(customer_id=4, arrival_time=3, ticket_type="VIP")
    customer5 = Customer(customer_id=5, arrival_time=4, ticket_type="Regular")

    customers = [customer1, customer2, customer3, customer4, customer5]

    # 2. Set up the Service Times Repository
    service_data = {
        "ticket_type": ["Regular", "VIP"],
        "service_time": [10.0, 5.0],  # Regular takes 10, VIP takes 5
    }
    service_times_df = pd.DataFrame(service_data)
    service_times_repo = DataFrameRepo(data=service_times_df)

    # 3. Initialize and populate the Priority Queue
    # PriorityQueueLeo uses a deque internally
    customer_queue = PriorityQueueLeo([])
    for cust in customers:
        customer_queue.enqueue(cust)

    # 4. Define parameters for update_queue_improved
    num_service_points: int = 1
    priority_ticket_types: Set[str] = {"VIP"}
    # VIPs should ideally wait less than 7 time units
    p_threshold: float = 7.0
    # Regular customers shouldn't have their wait time exceed 20 units due to a VIP skip
    non_p_threshold: float = 20.0

    # Print initial state
    print_queue_with_estimates(
        "Initial Queue State",
        customer_queue,
        num_service_points,
        service_times_repo,
        # current_time_val is 0.0 by default in print_queue_with_estimates
    )

    # 5. Call update_queue_improved
    optimized_queue = update_queue_improved(
        queue=customer_queue,
        service_times_repo=service_times_repo,
        service_points=num_service_points,
        priority_tickets=priority_ticket_types,
        p_threshold=p_threshold,
        non_p_threshold=non_p_threshold,
    )

    # Print final state
    print_queue_with_estimates(
        "Optimized Queue State",
        optimized_queue,
        num_service_points,
        service_times_repo,
        # current_time_val is 0.0 by default in print_queue_with_estimates
    )


def main():
    prueba_1()
    prueba_2()


if __name__ == "__main__":
    main()
