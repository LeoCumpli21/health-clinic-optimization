import pytest

from datetime import datetime, timedelta
from typing import List, Any, Optional

from src.entities.customer import Customer
from src.services.estimate_time_left import estimate_total_times_in_line
from src.interfaces.priority_queue import PriorityQueue
from src.interfaces.repository import Repository


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


# Define a base datetime for consistent testing
BASE_DATETIME = datetime(2025, 5, 26, 10, 0, 0)


def test_estimate_total_times_in_line_empty_queue():
    """Tests behavior with an empty queue. Expected: empty list."""
    queue = MockPriorityQueue([])
    repo_mock = MockRepository({})
    service_points = 2
    current_time = BASE_DATETIME + timedelta(minutes=10)
    result = estimate_total_times_in_line(
        service_points, queue, repo_mock, current_time
    )
    assert result == []


def test_estimate_total_times_in_line_single_customer():
    """Tests with a single customer in the queue."""
    arrival_time = BASE_DATETIME
    current_time = BASE_DATETIME + timedelta(minutes=5)
    customers = [Customer(1, arrival_time, "typeA")]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10.0})
    service_points = 2

    # Time already waited = 5.0 minutes
    # Estimated time left in queue = 0 / 2 = 0.0
    # Total estimated time = 5.0 + 0.0 = 5.0
    expected_total_time = 5.0

    result = estimate_total_times_in_line(
        service_points, queue, repo_mock, current_time
    )

    assert len(result) == 1
    assert result[0][0] == customers[0]
    assert result[0][1] == pytest.approx(expected_total_time)


def test_estimate_total_times_in_line_multiple_customers():
    """Tests with multiple customers, accumulating time."""
    c1_arrival = BASE_DATETIME
    c2_arrival = BASE_DATETIME + timedelta(minutes=1)
    current_time = BASE_DATETIME + timedelta(minutes=10)  # Current time is 10:10:00

    # Customer 1 (ID 100): arrives 10:00:00, service_time 5.0
    # Customer 2 (ID 101): arrives 10:01:00, service_time 10.0
    customers = [
        Customer(100, c1_arrival, "typeB"),
        Customer(101, c2_arrival, "typeA"),
    ]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10.0, "typeB": 5.0})
    service_points = 2

    # For Customer 1 (ID 100):
    # Time already waited = (10:10:00 - 10:00:00) = 10.0 mins
    # Estimated time left in queue (for C1) = 0 / 2 = 0.0 mins
    # Total est time C1 = 10.0 + 0.0 = 10.0 mins
    expected_total_time_c1 = 10.0

    # For Customer 2 (ID 101):
    # Time already waited = (10:10:00 - 10:01:00) = 9.0 mins
    # Estimated time left in queue (for C2, behind C1) = service_time_c1 / service_points = 5.0 / 2 = 2.5 mins
    # Total est time C2 = 9.0 + 2.5 = 11.5 mins
    expected_total_time_c2 = 11.5

    result = estimate_total_times_in_line(
        service_points, queue, repo_mock, current_time
    )

    assert len(result) == 2
    assert result[0][0] == customers[0]
    assert result[0][1] == pytest.approx(expected_total_time_c1)
    assert result[1][0] == customers[1]
    assert result[1][1] == pytest.approx(expected_total_time_c2)


def test_estimate_total_times_in_line_zero_service_points_with_customers():
    """Tests behavior when service_points is 0 and queue has customers.
    Expected: ZeroDivisionError.
    """
    arrival_time = BASE_DATETIME
    current_time = BASE_DATETIME + timedelta(minutes=5)
    customers = [Customer(1, arrival_time, "typeA")]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10.0})
    service_points = 0

    with pytest.raises(ZeroDivisionError):
        estimate_total_times_in_line(service_points, queue, repo_mock, current_time)


def test_estimate_total_times_in_line_zero_service_points_empty_queue():
    """Tests behavior when service_points is 0 and queue is empty.
    Expected: empty list, no division occurs.
    """
    queue = MockPriorityQueue([])
    repo_mock = MockRepository({})
    service_points = 0
    current_time = BASE_DATETIME + timedelta(minutes=10)
    result = estimate_total_times_in_line(
        service_points, queue, repo_mock, current_time
    )
    assert result == []


def test_estimate_total_times_in_line_customer_ticket_type_not_in_repo():
    """Tests when a customer's ticket type is not in the service times repository.
    The mock repository defaults to a service time of 0 for unknown types.
    """
    c1_arrival = BASE_DATETIME
    c2_arrival = BASE_DATETIME + timedelta(minutes=1)  # Arrives at 10:01:00
    current_time = BASE_DATETIME + timedelta(minutes=5)  # Current time is 10:05:00

    # Customer 1 (ID 1): arrives 10:00:00, typeA, service_time 10.0
    # Customer 2 (ID 2): arrives 10:01:00, typeC, service_time 0.0 (unknown)
    customers = [
        Customer(1, c1_arrival, "typeA"),
        Customer(2, c2_arrival, "typeC"),
    ]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10.0})  # typeC is not defined, defaults to 0
    service_points = 2

    # For Customer 1 (ID 1):
    # Time already waited = (10:05:00 - 10:00:00) = 5.0 mins
    # Estimated time left in queue (for C1) = 0 / 2 = 0.0 mins
    # Total est time C1 = 5.0 + 0.0 = 5.0 mins
    expected_total_time_c1 = 5.0

    # For Customer 2 (ID 2):
    # Time already waited = (10:05:00 - 10:01:00) = 4.0 mins
    # Estimated time left in queue (for C2, behind C1) = service_time_c1 / service_points = 10.0 / 2 = 5.0 mins
    # Total est time C2 = 4.0 + 5.0 = 9.0 mins
    expected_total_time_c2 = 9.0

    result = estimate_total_times_in_line(
        service_points, queue, repo_mock, current_time
    )

    assert len(result) == 2
    assert result[0][0] == customers[0]
    assert result[0][1] == pytest.approx(expected_total_time_c1)
    assert result[1][0] == customers[1]
    assert result[1][1] == pytest.approx(expected_total_time_c2)
