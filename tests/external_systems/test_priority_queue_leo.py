import pytest
from src.entities.customer import Customer
from src.external_systems.priority_queue_leo import PriorityQueueLeo


def test_enqueue_and_dequeue():
    # Create customers
    customer1 = Customer(customer_id=1, arrival_time=5, ticket_type="Regular")
    customer2 = Customer(customer_id=2, arrival_time=6, ticket_type="VIP")

    # Initialize the priority queue
    priority_queue = PriorityQueueLeo()

    # Enqueue customers
    priority_queue.enqueue(customer1, priority=2)
    priority_queue.enqueue(customer2, priority=1)

    # Dequeue customers and check order
    assert priority_queue.dequeue() == customer2  # VIP customer has higher priority
    assert priority_queue.dequeue() == customer1  # Regular customer is next
    assert priority_queue.dequeue() is None  # Queue should be empty


def test_update_priority():
    # Create customers
    customer1 = Customer(customer_id=1, arrival_time=5, ticket_type="Regular")
    customer2 = Customer(customer_id=2, arrival_time=6, ticket_type="VIP")
    customer3 = Customer(customer_id=3, arrival_time=7, ticket_type="VIP")

    # Initialize the priority queue
    priority_queue = PriorityQueueLeo()

    # Enqueue customers
    priority_queue.enqueue(customer1, priority=3)
    priority_queue.enqueue(customer2, priority=1)
    priority_queue.enqueue(customer3, priority=2)

    # Update priority of customer1
    priority_queue.update_priority(
        customer_id=1, new_priority=0, priority_ticket_types={"VIP"}
    )

    # Check updated order
    assert (
        priority_queue.dequeue().customer_id == customer1.customer_id
    )  # Customer1 now has the highest priority
    assert (
        priority_queue.dequeue().customer_id == customer2.customer_id
    )  # Customer2 is next
    assert (
        priority_queue.dequeue().customer_id == customer3.customer_id
    )  # Customer3 is last


def test_print_queue(capsys):
    # Create customers
    customer1 = Customer(customer_id=1, arrival_time=5, ticket_type="Regular")
    customer2 = Customer(customer_id=2, arrival_time=6, ticket_type="VIP")

    # Initialize the priority queue
    priority_queue = PriorityQueueLeo()

    # Enqueue customers
    priority_queue.enqueue(customer1, priority=2)
    priority_queue.enqueue(customer2, priority=1)

    # Print queue
    priority_queue.print_queue()

    # Capture printed output
    captured = capsys.readouterr()
    assert "Priority: 1, Customer ID: 2, Ticket Type: VIP" in captured.out
    assert "Priority: 2, Customer ID: 1, Ticket Type: Regular" in captured.out
