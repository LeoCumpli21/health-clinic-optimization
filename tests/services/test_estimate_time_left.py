import pytest
from src.entities.customer import Customer
from src.services.estimate_time_left import estimate_times_left
from src.interfaces.priority_queue import PriorityQueue
from src.interfaces.repository import Repository
from typing import List, Any, Optional


# Mock PriorityQueue to simulate the queue behavior
class MockPriorityQueue(PriorityQueue):
    def __init__(self, customers_list: List[Customer]):
        super().__init__(customers_list)  # Initialize base class
        self.customers_list = customers_list

    def __iter__(self):
        return iter(self.customers_list)

    def __len__(self) -> int:
        return len(self.customers_list)

    # Implement abstract methods from PriorityQueue, even if not used by these specific tests
    def enqueue(self, customer: Customer) -> None:
        pass

    def dequeue(self) -> Optional[Customer]:
        pass

    def update_priority(self, customer: Customer, new_position: int) -> None:
        pass

    def print_queue(self) -> None:
        pass


# Helper class to mock DataFrame behavior (remains the same)
class MockDataFrame:
    def __init__(self, data_list):
        self.data_list = data_list

    @property
    def iloc(self):
        return self.data_list


# Mock Repository to simulate fetching service times
class MockRepository(Repository):
    def __init__(self, service_times_map: dict[str, float]):
        self.service_times_map = service_times_map

    def get_data(self, filters: Any) -> Any:  # Match interface signature
        ticket_type = filters.get("ticket_type")
        service_time = self.service_times_map.get(ticket_type, 0)
        return MockDataFrame([{"service_time": service_time}])


def test_estimate_times_left_empty_queue():
    """Tests behavior with an empty queue. Expected: empty list."""
    queue = MockPriorityQueue([])
    repo_mock = MockRepository({})
    service_points = 2
    result = estimate_times_left(service_points, queue, repo_mock)
    assert result == []


def test_estimate_times_left_single_customer():
    """Tests with a single customer in the queue."""
    customers = [Customer(1, 5, "typeA")]  # customer_id is now int
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10})
    service_points = 2
    # Expected: service_time (10) / service_points (2) = 5.0

    result = estimate_times_left(service_points, queue, repo_mock)

    assert len(result) == 1
    assert result[0][0] == customers[0]  # Check customer object
    assert result[0][1] == pytest.approx(5.0)


def test_estimate_times_left_multiple_customers():
    """Tests with multiple customers, accumulating time."""
    customers = [
        Customer(100, 5, "typeB"),  # Service time 5, customer_id is int
        Customer(101, 6, "typeA"),  # Service time 10, customer_id is int
    ]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10, "typeB": 5})
    service_points = 2

    # Expected for customer 100: service_time_c0 (5) / 2 = 2.5
    # Expected for customer 101: (service_time_c0 (5) + service_time_c1 (10)) / 2 = 15 / 2 = 7.5

    result = estimate_times_left(service_points, queue, repo_mock)

    assert len(result) == 2
    assert result[0][0] == customers[0]
    assert result[0][1] == pytest.approx(2.5)
    assert result[1][0] == customers[1]
    assert result[1][1] == pytest.approx(7.5)


def test_estimate_times_left_zero_service_points_with_customers():
    """Tests behavior when service_points is 0 and queue has customers.
    Expected: ZeroDivisionError.
    """
    customers = [Customer(1, 5, "typeA")]  # customer_id is int
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10})
    service_points = 0

    with pytest.raises(ZeroDivisionError):
        estimate_times_left(service_points, queue, repo_mock)


def test_estimate_times_left_zero_service_points_empty_queue():
    """Tests behavior when service_points is 0 and queue is empty.
    Expected: empty list, no division occurs.
    """
    queue = MockPriorityQueue([])
    repo_mock = MockRepository({})
    service_points = 0
    result = estimate_times_left(service_points, queue, repo_mock)
    assert result == []


def test_estimate_times_left_customer_ticket_type_not_in_repo():
    """Tests when a customer's ticket type is not in the service times repository.
    The mock repository defaults to a service time of 0 for unknown types.
    """
    customers = [
        Customer(1, 1, "typeA"),  # Service time 10, customer_id is int
        Customer(2, 2, "typeC"),  # Service time 0 (unknown type), customer_id is int
    ]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10})  # typeC is not defined, defaults to 0
    service_points = 2

    # Expected for customer 1: service_time_c1 (10) / 2 = 5.0
    # Expected for customer 2: (service_time_c1 (10) + service_time_c2 (0)) / 2 = 10 / 2 = 5.0

    result = estimate_times_left(service_points, queue, repo_mock)

    assert len(result) == 2
    assert result[0][0] == customers[0]
    assert result[0][1] == pytest.approx(5.0)
    assert result[1][0] == customers[1]
    assert result[1][1] == pytest.approx(5.0)
