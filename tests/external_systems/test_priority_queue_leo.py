import pytest
from datetime import datetime, timedelta  # Added datetime and timedelta
from src.entities.customer import Customer
from src.external_systems.priority_queue_leo import PriorityQueueLeo

# Define a base datetime for consistent testing
BASE_DATETIME = datetime(2025, 5, 26, 12, 0, 0)


def test_enqueue_and_dequeue():
    # Create customers with datetime arrival_time
    customer1 = Customer(
        customer_id=1, arrival_time=BASE_DATETIME, ticket_type="Regular"
    )
    customer2 = Customer(
        customer_id=2,
        arrival_time=BASE_DATETIME + timedelta(minutes=1),
        ticket_type="VIP",
    )

    # Initialize the priority queue with an empty list
    priority_queue = PriorityQueueLeo([])  # Enqueue customers
    priority_queue.enqueue(customer1)  # No priority argument
    priority_queue.enqueue(customer2)  # No priority argument

    # Dequeue customers and check order (FIFO because enqueue is append, dequeue is popleft)
    # customer1 was enqueued first (to the right), then customer2 (to the right of customer1).
    # So deque is [customer1, customer2]
    # popleft() removes from the left, so customer1 is dequeued first.
    assert priority_queue.dequeue() == customer1
    assert priority_queue.dequeue() == customer2
    assert priority_queue.dequeue() is None  # Queue should be empty


def test_update_priority():
    # Create customers with datetime arrival_time
    customer1 = Customer(
        customer_id=1, arrival_time=BASE_DATETIME, ticket_type="Regular"
    )
    customer2 = Customer(
        customer_id=2,
        arrival_time=BASE_DATETIME + timedelta(minutes=1),
        ticket_type="VIP",
    )
    customer3 = Customer(
        customer_id=3,
        arrival_time=BASE_DATETIME + timedelta(minutes=2),
        ticket_type="VIP",
    )  # Initialize the priority queue with customers
    # Initial order in deque: [customer1, customer2, customer3] (due to append)
    priority_queue = PriorityQueueLeo([customer1, customer2, customer3])

    # Update position of customer3 to be the first to be dequeued (index 0)
    # Current deque: [customer1, customer2, customer3]
    # To make customer3 dequeued first, it needs to be at the leftmost end (index 0).
    # Move customer3 to index 0
    priority_queue.update_priority(customer3, 0)
    # Deque after moving customer3 to index 0: [customer3, customer1, customer2]
    # Dequeue order: customer3, customer1, customer2

    assert priority_queue.dequeue() == customer3
    assert priority_queue.dequeue() == customer1
    assert priority_queue.dequeue() == customer2
    assert priority_queue.dequeue() is None


def test_print_queue(capsys):
    # Create customers with datetime arrival_time
    customer1 = Customer(
        customer_id=1, arrival_time=BASE_DATETIME, ticket_type="Regular"
    )
    customer2 = Customer(
        customer_id=2,
        arrival_time=BASE_DATETIME + timedelta(minutes=1),
        ticket_type="VIP",
    )  # Initialize the priority queue
    # Enqueue order: customer1, then customer2. Deque: [customer1, customer2]
    priority_queue = PriorityQueueLeo([])
    priority_queue.enqueue(customer1)
    priority_queue.enqueue(customer2)

    # Print queue
    priority_queue.print_queue()

    # Capture printed output
    # Deque is [customer1, customer2]. Iteration order is [customer1, customer2]
    # Rank 1 (highest priority, dequeued first) is customer1.
    # Rank 2 is customer2.
    captured = capsys.readouterr()
    assert "Rank: 1, Customer ID: 1, Ticket Type: Regular" in captured.out
    assert "Rank: 2, Customer ID: 2, Ticket Type: VIP" in captured.out
