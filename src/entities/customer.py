class Customer:
    def __init__(self, customer_id: int, arrival_time, ticket_type: str):
        self.customer_id = customer_id
        self.arrival_time = arrival_time
        self.ticket_type = ticket_type

    def __lt__(self, other):
        return self.customer_id < other.customer_id
