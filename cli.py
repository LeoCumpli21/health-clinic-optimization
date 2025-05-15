from src.entities.customer import Customer
from src.external_systems.priority_queue_leo import PriorityQueueLeo

# Create some example customers
customer1 = Customer(customer_id=1, arrival_time=5, ticket_type="Regular")
customer2 = Customer(customer_id=2, arrival_time=6, ticket_type="VIP")
customer3 = Customer(customer_id=3, arrival_time=7, ticket_type="VIP")
customer4 = Customer(customer_id=4, arrival_time=8, ticket_type="Regular")

# Initialize the priority queue
priority_queue = PriorityQueueLeo()

# Enqueue customers with their priorities
priority_queue.enqueue(customer1, priority=2)
priority_queue.enqueue(customer2, priority=0)
priority_queue.enqueue(customer3, priority=1)
priority_queue.enqueue(customer4, priority=4)

priority_queue.print_queue()

# Dequeue the customer with the highest priority (lowest priority value)
highest_priority_customer = priority_queue.dequeue()
print(f"Dequeued customer: {highest_priority_customer.customer_id}")


priority_queue.print_queue()

# Update the priority of a specific customer
priority_queue.update_priority(
    customer_id=1, new_priority=0, priority_ticket_types={"VIP"}
)
print("After updating priority of customer 1 to highest:")
priority_queue.print_queue()
