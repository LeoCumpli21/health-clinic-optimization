from datetime import datetime, timedelta

from typing import Set

from src.entities.customer import Customer
from src.external_systems.priority_queue_leo import PriorityQueueLeo
from src.external_systems.dataframe_repo import DataFrameRepo
from src.interfaces.repository import Repository
from src.interfaces.priority_queue import PriorityQueue as PriorityQueueInterface
from src.services.manipulate_queue import update_queue_improved
from src.services.estimate_time_left import (
    estimate_total_times_in_line,
)
from src.services import simulate_arrivals
from src.services.clinic_queue_simulation import ClinicQueueSimulator
from src import utils

import pandas as pd


SUCURSAL = "CULIACAN COLEGIO MILITAR"
START_TIME_SIMULATION_STR = "2025-05-12 00:00:00"
SIMULATION_DURATION_DAYS = 28
CHOSEN_DATE = datetime(2025, 5, 12, 0, 0, 0)


def _get_data_one_day_data(data: pd.DataFrame, date_time: datetime) -> pd.DataFrame:
    """Helper function to filter data for a specific date."""
    return (
        data[data["SimulatedTurnoInicioDateTime"].dt.date == date_time.date()]
        .sort_values(by="SimulatedTurnoInicioDateTime")
        .reset_index(drop=True)
    )


def _build_customer_list(arrivals: pd.DataFrame) -> list[Customer]:
    """Helper function to build a list of Customer objects from a DataFrame of arrivals."""
    customers = []
    ix = 0
    for _, row in arrivals.iterrows():
        customer = Customer(
            customer_id=ix,
            arrival_time=row["SimulatedTurnoInicioDateTime"],
            ticket_type=row["Group"],
        )
        customers.append(customer)
        ix += 1
    return customers


def prueba_1():
    # Define a base time for arrival times
    base_time_p1 = datetime(2025, 5, 26, 8, 0, 0)

    # Create some example customers with datetime arrival_time
    customer1 = Customer(
        customer_id=1,
        arrival_time=base_time_p1 + timedelta(minutes=5),
        ticket_type="Regular",
    )
    customer2 = Customer(
        customer_id=2,
        arrival_time=base_time_p1 + timedelta(minutes=6),
        ticket_type="VIP",
    )
    customer3 = Customer(
        customer_id=3,
        arrival_time=base_time_p1 + timedelta(minutes=7),
        ticket_type="VIP",
    )
    customer4 = Customer(
        customer_id=4,
        arrival_time=base_time_p1 + timedelta(minutes=8),
        ticket_type="Regular",
    )

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
        current_time_val: datetime,  # Changed type to datetime
    ):
        print(f"\n--- {header} ---")
        if len(queue_to_print) > 0:
            # Use estimate_total_times_in_line and pass current_time_val
            estimates = estimate_total_times_in_line(
                service_points_val, queue_to_print, repo, current_time_val
            )
            print(
                "Queue Order (ID, Type, Arrival): Total Estimated Time (waited + future, in mins)"
            )

            q_iterable = (
                queue_to_print.queue
                if hasattr(queue_to_print, "queue")
                else queue_to_print
            )

            for i, customer_obj in enumerate(q_iterable):
                # estimates contains (Customer, total_estimated_time)
                # We need to find the estimate for the current customer_obj
                # Assuming estimates are in the same order as q_iterable
                est_total_time = estimates[i][1]
                arrival_fmt = customer_obj.arrival_time.strftime("%H:%M:%S")
                print(
                    f"{i+1}. C{customer_obj.customer_id} ({customer_obj.ticket_type}, Arr@{arrival_fmt}): "
                    f"Total Est. Time={est_total_time:.2f} min"
                )
        else:
            print("Queue is empty.")
        print("-" * (len(header) + 8))

        # 1. Create Customer objects with datetime arrival_time

    base_time_p2 = datetime(2025, 5, 26, 9, 0, 0)  # Base time for prueba_2 arrivals
    current_eval_time = base_time_p2 + timedelta(
        minutes=10
    )  # Example current time for evaluation

    customer1 = Customer(
        customer_id=1,
        arrival_time=base_time_p2 + timedelta(minutes=0),
        ticket_type="Regular",
    )
    customer2 = Customer(
        customer_id=2,
        arrival_time=base_time_p2 + timedelta(minutes=1),
        ticket_type="VIP",
    )
    customer3 = Customer(
        customer_id=3,
        arrival_time=base_time_p2 + timedelta(minutes=2),
        ticket_type="Regular",
    )
    customer4 = Customer(
        customer_id=4,
        arrival_time=base_time_p2 + timedelta(minutes=3),
        ticket_type="VIP",
    )
    customer5 = Customer(
        customer_id=5,
        arrival_time=base_time_p2 + timedelta(minutes=4),
        ticket_type="Regular",
    )

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
        current_eval_time,  # Pass current_eval_time
    )

    # 5. Call update_queue_improved with current_time
    optimized_queue = update_queue_improved(
        queue=customer_queue,
        service_times_repo=service_times_repo,
        service_points=num_service_points,
        priority_tickets=priority_ticket_types,
        p_threshold=p_threshold,
        non_p_threshold=non_p_threshold,
        current_time=current_eval_time,  # Pass current_eval_time
    )

    # Print final state
    print_queue_with_estimates(
        "Optimized Queue State",
        optimized_queue,
        num_service_points,
        service_times_repo,
        current_eval_time,  # Pass current_eval_time
    )


def simulate_arrivals_prueba_3():
    sd_data = pd.read_pickle("data/data_for_queueing_model.pkl")
    print("Data loaded successfully.")
    print(sd_data.info())
    lambda_t_df = utils.get_arrival_rates(sd_data)
    np_simulated_data_df = simulate_arrivals.run_arrival_simulation(
        full_arrival_rates_df=lambda_t_df,
        sucursal_to_simulate=SUCURSAL,
        group_to_simulate="NP",
        sim_start_datetime_str=START_TIME_SIMULATION_STR,
        sim_duration_days=SIMULATION_DURATION_DAYS,
    )
    p_simulated_data_df = simulate_arrivals.run_arrival_simulation(
        full_arrival_rates_df=lambda_t_df,
        sucursal_to_simulate=SUCURSAL,
        group_to_simulate="P",
        sim_start_datetime_str=START_TIME_SIMULATION_STR,
        sim_duration_days=SIMULATION_DURATION_DAYS,
    )
    simulated_data_df = pd.concat(
        [np_simulated_data_df, p_simulated_data_df], ignore_index=True
    )
    print("Simulation completed successfully.")
    return simulated_data_df


def run_full_clinic_simulation(simulated_data_df: pd.DataFrame):
    """Run a full clinic queueing simulation for one day."""
    print("\n\n" + "=" * 70)
    print("           RUNNING FULL CLINIC QUEUE SIMULATION")
    print("=" * 70)

    # Filter the simulated data for the chosen date
    arrivals_for_chosen_date = _get_data_one_day_data(simulated_data_df, CHOSEN_DATE)

    print(f"Date: {CHOSEN_DATE.date()}")
    print(f"Total arrivals for this day: {len(arrivals_for_chosen_date)}")
    print(
        f"Priority (P) customers: {len(arrivals_for_chosen_date[arrivals_for_chosen_date['Group'] == 'P'])}"
    )
    print(
        f"Non-priority (NP) customers: {len(arrivals_for_chosen_date[arrivals_for_chosen_date['Group'] == 'NP'])}"
    )

    # Setup service times based on real data analysis
    service_data = {
        "ticket_type": ["P", "NP"],
        "service_time": [2.539955, 3.448537],  # Average from real data
    }
    service_times_df = pd.DataFrame(service_data)
    service_times_repo = DataFrameRepo(data=service_times_df)

    # Create simulator with different configurations
    configurations = [
        {
            "name": "Current System (No Priority Aging)",
            "num_service_windows": 4,  # Reduced to create congestion
            "p_threshold_minutes": float("inf"),  # No optimization
            "non_p_threshold_minutes": float("inf"),
            "optimization_enabled": False,
        },
        {
            "name": "Optimized System (With Priority Aging)",
            "num_service_windows": 4,  # Reduced to create congestion
            "p_threshold_minutes": 7.0,  # Priority customers should wait max 30 min (more realistic)
            "non_p_threshold_minutes": 20.0,  # Non-priority max 80 min (more realistic for high load)
            "optimization_enabled": True,
        },
    ]

    results = {}

    for config in configurations:
        print(f"\n--- Running: {config['name']} ---")

        # Create simulator
        simulator = ClinicQueueSimulator(
            num_service_windows=config["num_service_windows"],
            opening_hour=6,  # Based on real data
            closing_hour=18,  # Based on real data
            priority_tickets={"P"},
            p_threshold_minutes=config["p_threshold_minutes"],
            non_p_threshold_minutes=config["non_p_threshold_minutes"],
            service_times_repo=service_times_repo,
        )  # Run simulation
        optimization_interval = (
            1 if config["optimization_enabled"] else 999999
        )  # Large number to effectively disable

        # Enable debugging for the optimized system to see queue movements
        debug_optimization = config["optimization_enabled"]

        simulation_state = simulator.simulate_day(
            arrivals_df=arrivals_for_chosen_date,
            simulation_date=CHOSEN_DATE,
            optimization_interval_minutes=optimization_interval,
            verbose=True,
            debug_optimization=debug_optimization,
        )

        # Print results
        simulation_state.print_summary()
        results[config["name"]] = simulation_state.get_summary_dict()

    # Compare results
    print("\n" + "=" * 70)
    print("                    COMPARISON RESULTS")
    print("=" * 70)

    current_system = results["Current System (No Priority Aging)"]
    optimized_system = results["Optimized System (With Priority Aging)"]

    print(f"{'Metric':<35} {'Current':<15} {'Optimized':<15} {'Improvement'}")
    print("-" * 70)

    metrics_to_compare = [
        ("Service Rate (%)", "service_rate_percentage", "%"),
        ("Avg Wait Time (min)", "avg_wait_time_minutes", "min"),
        ("Max Wait Time (min)", "max_wait_time_minutes", "min"),
        ("Customers > 20min wait", "customers_waiting_over_20_min", "count"),
        ("% Customers > 20min", "percentage_waiting_over_20_min", "%"),
    ]

    for metric_name, metric_key, unit in metrics_to_compare:
        current_val = current_system.get(metric_key)
        optimized_val = optimized_system.get(metric_key)

        if current_val is not None and optimized_val is not None:
            if metric_key in [
                "avg_wait_time_minutes",
                "max_wait_time_minutes",
                "customers_waiting_over_20_min",
                "percentage_waiting_over_20_min",
            ]:
                # Lower is better
                improvement = (
                    ((current_val - optimized_val) / current_val * 100)
                    if current_val != 0
                    else 0
                )
                improvement_str = f"{improvement:+.1f}%"
            else:
                # Higher is better
                improvement = (
                    ((optimized_val - current_val) / current_val * 100)
                    if current_val != 0
                    else 0
                )
                improvement_str = f"{improvement:+.1f}%"

            print(
                f"{metric_name:<35} {current_val:<15.2f} {optimized_val:<15.2f} {improvement_str}"
            )
        else:
            print(f"{metric_name:<35} {'N/A':<15} {'N/A':<15} {'N/A'}")

    print("=" * 70)

    return results


def run_queue_simulation(simulated_data_df: pd.DataFrame):
    print("\n\nRunning basic queue state analysis...\n")
    # Filter the simulated data for the chosen date
    arrivals_for_chosen_date = _get_data_one_day_data(simulated_data_df, CHOSEN_DATE)
    customer_list = _build_customer_list(arrivals_for_chosen_date)
    # Initialize the priority queue with the customer list
    priority_queue = PriorityQueueLeo(customer_list)
    # Print the initial queue state (first 100 customers)
    print("Initial Queue State (first 100 customers):")
    for i, customer in enumerate(priority_queue.queue):
        if i >= 100:
            print(f"... and {len(priority_queue.queue) - 100} more customers")
            break
        print(
            f"Rank: {i+1}, Customer ID: {customer.customer_id}, Ticket Type: {customer.ticket_type}"
        )


def main():
    print("=" * 70)
    print("     HEALTH CLINIC QUEUE OPTIMIZATION SIMULATION")
    print("=" * 70)

    # Skip the simple tests for now and focus on the full simulation
    print("Running arrival simulation...")
    simulated_data_df = simulate_arrivals_prueba_3()

    # Run basic queue analysis (existing functionality)
    run_queue_simulation(simulated_data_df)

    # Run full clinic simulation (NEW!)
    run_full_clinic_simulation(simulated_data_df)

    print("\n" + "=" * 70)
    print("All simulations completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
