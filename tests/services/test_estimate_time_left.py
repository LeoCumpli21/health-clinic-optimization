import pytest
from src.entities.customer import Customer
from src.services.estimate_time_left import estimate_time_left


# Mock PriorityQueue to simulate the queue behavior
class MockPriorityQueue:
    def __init__(self, customers_list):
        self.customers_list = customers_list

    def __iter__(self):
        return iter(self.customers_list)


# Helper class to mock DataFrame behavior
class MockDataFrame:
    def __init__(self, data_list):
        self.data_list = data_list

    @property
    def iloc(self):
        # This makes it so that accessing .iloc returns the list,
        # and then .iloc[0] accesses the first element of that list.
        return self.data_list


# Mock Repository to simulate fetching service times
class MockRepository:
    def __init__(self, service_times_map):
        # service_times_map is a dict mapping ticket_type to service_time
        self.service_times_map = service_times_map

    def get_data(self, query_dict):
        ticket_type = query_dict.get("ticket_type")
        service_time = self.service_times_map.get(
            ticket_type, 0
        )  # Default to 0 if type not found
        # Return an object that mimics DataFrame.iloc[0]["service_time"]
        # The list wrapper is for .iloc, and the dict is for ["service_time"]
        return MockDataFrame([{"service_time": service_time}])


def test_estimate_time_left_empty_queue():
    """
    Tests behavior with an empty queue.
    Expected: 0, as the loop won't run and it returns the default 0.
    """
    queue = MockPriorityQueue([])
    repo_mock = MockRepository({})
    assert estimate_time_left("c1", 2, queue, repo_mock) == 0


def test_estimate_time_left_customer_first_in_queue():
    """
    Tests when the target customer is the first in the queue.
    Expected: 0, as time_left is 0 before this customer.
    """
    customers = [Customer("c1", 5, "typeA")]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10})
    assert estimate_time_left("c1", 2, queue, repo_mock) == 0


def test_estimate_time_left_customer_later_in_queue():
    """
    Tests when the target customer is not the first in the queue.
    The time_left should accumulate for customers ahead.
    """
    customers = [Customer("c0", 5, "typeB"), Customer("c1", 6, "typeA")]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10, "typeB": 5})  # c0 takes 5 units of time
    # Expected: time_left for c0 (5) / service_points (2) = 2.5
    assert estimate_time_left("c1", 2, queue, repo_mock) == 2.5


def test_estimate_time_left_customer_not_in_queue():
    """
    Tests when the target customer is not in the queue.
    Expected: 0, as the function returns the default 0 after the loop.
    """
    customers = [Customer("c0", 5, "typeB"), Customer("c2", 6, "typeC")]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeB": 5, "typeC": 8})
    assert estimate_time_left("c1", 2, queue, repo_mock) == 0


def test_estimate_time_left_customer_found_zero_service_points():
    """
    Tests when customer is found and service_points is 0.
    Expected: ZeroDivisionError, as time_left (0 for the first customer) / 0.
    """
    customers = [Customer("c1", 5, "typeA")]
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10})
    with pytest.raises(ZeroDivisionError):
        estimate_time_left("c1", 0, queue, repo_mock)


def test_estimate_time_left_customer_not_found_zero_service_points():
    """
    Tests when customer is not found and service_points is 0.
    Expected: 0, as the function returns the default 0 after the loop,
              and no division by zero occurs.
    """
    customers = [Customer("c2", 5, "typeA")]  # Target "c1" is not in queue
    queue = MockPriorityQueue(customers)
    repo_mock = MockRepository({"typeA": 10})
    assert estimate_time_left("c1", 0, queue, repo_mock) == 0
