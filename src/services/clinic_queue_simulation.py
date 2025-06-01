"""
Main clinic queueing simulation module.

This module implements a discrete event simulation of a health clinic's queueing system.
It handles customer arrivals, queue management with priority aging, service window allocation,
and tracks comprehensive metrics for performance analysis.
"""

from datetime import datetime, timedelta
from typing import List, Set, Optional
import pandas as pd

from src.entities.customer import Customer
from src.entities.service_window import ServiceWindow
from src.entities.clinic_simulation_state import ClinicSimulationState
from src.external_systems.priority_queue_leo import PriorityQueueLeo
from src.external_systems.dataframe_repo import DataFrameRepo
from src.services.manipulate_queue import update_queue_improved
from src.services.estimate_time_left import get_estimated_service_time
from src.interfaces.repository import Repository


class ClinicQueueSimulator:
    """Simulates a clinic's queueing system with priority aging."""

    def __init__(
        self,
        num_service_windows: int = 3,
        opening_hour: int = 6,
        closing_hour: int = 18,
        priority_tickets: Optional[Set[str]] = None,
        p_threshold_minutes: float = 10.0,
        non_p_threshold_minutes: float = 20.0,
        service_times_repo: Optional[Repository] = None,
    ):
        """
        Initialize the clinic simulator.

        Args:
            num_service_windows: Number of service windows available
            opening_hour: Clinic opening hour (24-hour format)
            closing_hour: Clinic closing hour (24-hour format)
            priority_tickets: Set of ticket types considered priority
            p_threshold_minutes: Maximum wait time threshold for priority customers
            non_p_threshold_minutes: Maximum wait time threshold for non-priority customers
            service_times_repo: Repository for service times by ticket type
        """
        self.num_service_windows = num_service_windows
        self.opening_hour = opening_hour
        self.closing_hour = closing_hour
        self.priority_tickets = priority_tickets or {"P"}
        self.p_threshold_minutes = p_threshold_minutes
        self.non_p_threshold_minutes = non_p_threshold_minutes

        # Set up default service times if none provided
        if service_times_repo is None:
            service_data = {
                "ticket_type": ["P", "NP"],
                "service_time": [3.32, 4.15],  # Based on real data average
            }
            service_times_df = pd.DataFrame(service_data)
            self.service_times_repo = DataFrameRepo(data=service_times_df)
        else:
            self.service_times_repo = service_times_repo

        # Initialize simulation components
        self.service_windows: List[ServiceWindow] = []
        self.queue = PriorityQueueLeo([])
        self.simulation_state = ClinicSimulationState()

        # Event tracking
        self.pending_arrivals: List[Customer] = []
        self.current_time: Optional[datetime] = None

    def setup_service_windows(self) -> None:
        """Initialize all service windows."""
        self.service_windows = [
            ServiceWindow(i) for i in range(self.num_service_windows)
        ]

    def load_arrivals(self, arrivals_df: pd.DataFrame) -> None:
        """
        Load customer arrivals from a DataFrame.

        Args:
            arrivals_df: DataFrame with columns ['SimulatedTurnoInicioDateTime', 'Group']
        """
        self.pending_arrivals = []

        # Filter for clinic operating hours
        arrivals_df = arrivals_df.copy()
        arrivals_df["hour"] = arrivals_df["SimulatedTurnoInicioDateTime"].dt.hour
        arrivals_df = arrivals_df[
            (arrivals_df["hour"] >= self.opening_hour)
            & (arrivals_df["hour"] < self.closing_hour)
        ]

        # Sort by arrival time
        arrivals_df = arrivals_df.sort_values(
            "SimulatedTurnoInicioDateTime"
        ).reset_index(drop=True)

        # Create Customer objects
        ix = 0
        for idx, row in arrivals_df.iterrows():
            customer = Customer(
                customer_id=ix,
                arrival_time=row["SimulatedTurnoInicioDateTime"],
                ticket_type=row["Group"],
            )
            self.pending_arrivals.append(customer)
            ix += 1

    def process_arrivals(self, current_time: datetime) -> None:
        """Process all customer arrivals up to the current time."""
        new_arrivals = []

        # Find customers arriving at or before current time
        remaining_arrivals = []
        for customer in self.pending_arrivals:
            if customer.arrival_time <= current_time:
                new_arrivals.append(customer)
            else:
                remaining_arrivals.append(customer)

        self.pending_arrivals = remaining_arrivals

        # Add new arrivals to queue and record in simulation state
        for customer in new_arrivals:
            self.queue.enqueue(customer)
            self.simulation_state.add_customer_arrival(customer)

    def process_service_completions(self, current_time: datetime) -> None:
        """Process service completions and free up windows."""
        for window in self.service_windows:
            if not window.is_available and window.is_service_complete(current_time):
                completed_customer = window.finish_service()
                if completed_customer:
                    self.simulation_state.record_service_completion(
                        completed_customer, current_time
                    )

    def assign_customers_to_windows(self, current_time: datetime) -> None:
        """Assign waiting customers to available service windows."""
        for window in self.service_windows:
            if window.is_available and len(self.queue) > 0:
                # Get next customer from queue
                customer = self.queue.dequeue()
                if customer:
                    # Calculate service time
                    service_time_minutes = get_estimated_service_time(
                        customer, self.service_times_repo
                    )
                    service_end_time = current_time + timedelta(
                        minutes=service_time_minutes
                    )

                    # Start service
                    window.start_service(customer, service_end_time)
                    self.simulation_state.record_service_start(customer, current_time)

    def optimize_queue(self, current_time: datetime, debug: bool = False) -> None:
        """Apply queue optimization algorithm."""
        if len(self.queue) > 1:  # Only optimize if there are multiple customers
            # Debug: Check queue state before optimization
            queue_length_before = len(self.queue)
            priority_customers_before = sum(
                1 for c in self.queue if c.ticket_type in self.priority_tickets
            )

            if debug:
                print(
                    f"\n🕐 OPTIMIZATION TRIGGERED at {current_time.strftime('%H:%M')}"
                )
                print(
                    f"   Queue length: {queue_length_before}, Priority customers: {priority_customers_before}"
                )

            self.queue = update_queue_improved(
                queue=self.queue,
                service_times_repo=self.service_times_repo,
                service_points=self.num_service_windows,
                priority_tickets=self.priority_tickets,
                p_threshold=self.p_threshold_minutes,
                non_p_threshold=self.non_p_threshold_minutes,
                current_time=current_time,
                debug=debug,
            )

            # Debug: Check if anything changed
            queue_length_after = len(self.queue)
            priority_customers_after = sum(
                1 for c in self.queue if c.ticket_type in self.priority_tickets
            )

            # Print debug info occasionally (reduced frequency when not in debug mode)
            if not debug and current_time.minute % 30 == 0:  # Every 30 minutes
                print(
                    f"  Optimization at {current_time.strftime('%H:%M')}: Queue={queue_length_before}, Priority={priority_customers_before}"
                )

    def handle_closing_time(self, closing_time: datetime) -> None:
        """Handle customers left in queue at closing time."""
        while len(self.queue) > 0:
            customer = self.queue.dequeue()
            if customer:
                self.simulation_state.record_customer_left_at_closing(
                    customer, closing_time
                )

    def get_next_event_time(self, current_time: datetime) -> Optional[datetime]:
        """
        Determine the next event time (arrival or service completion).

        Returns:
            Next event time, or None if no more events
        """
        next_times = []

        # Next arrival
        if self.pending_arrivals:
            next_times.append(
                self.pending_arrivals[0].arrival_time
            )  # Next service completion
        for window in self.service_windows:
            if not window.is_available and window.service_end_time:
                next_times.append(window.service_end_time)

        if not next_times:
            return None

        return min(next_times)

    def simulate_day(
        self,
        arrivals_df: pd.DataFrame,
        simulation_date: datetime,
        optimization_interval_minutes: int = 10,
        verbose: bool = False,
        debug_optimization: bool = False,
    ) -> ClinicSimulationState:
        """
        Simulate a full day of clinic operations.

        Args:
            arrivals_df: DataFrame with customer arrivals
            simulation_date: Date to simulate (time will be set to opening hour)
            optimization_interval_minutes: How often to run queue optimization
            verbose: Whether to print detailed progress
            debug_optimization: Whether to print detailed optimization debugging info

        Returns:
            ClinicSimulationState with simulation results
        """
        # Initialize simulation
        opening_time = simulation_date.replace(
            hour=self.opening_hour, minute=0, second=0, microsecond=0
        )
        closing_time = simulation_date.replace(
            hour=self.closing_hour, minute=0, second=0, microsecond=0
        )

        self.setup_service_windows()
        self.load_arrivals(arrivals_df)
        self.simulation_state = ClinicSimulationState()
        self.simulation_state.simulation_start_time = opening_time
        self.simulation_state.simulation_end_time = closing_time

        self.current_time = opening_time
        last_optimization_time = opening_time

        if verbose:
            print(f"Starting simulation for {simulation_date.date()}")
            print(f"Operating hours: {self.opening_hour}:00 - {self.closing_hour}:00")
            print(f"Service windows: {self.num_service_windows}")
            print(f"Total arrivals to process: {len(self.pending_arrivals)}")

        # Main simulation loop
        while self.current_time < closing_time:
            # Process arrivals
            self.process_arrivals(self.current_time)

            # Process service completions
            self.process_service_completions(self.current_time)

            # Assign customers to available windows
            self.assign_customers_to_windows(
                self.current_time
            )  # Periodic queue optimization
            if (
                self.current_time - last_optimization_time
            ).total_seconds() >= optimization_interval_minutes * 60:
                self.optimize_queue(self.current_time, debug=debug_optimization)
                last_optimization_time = self.current_time

            # Progress reporting
            if verbose and self.current_time.minute == 0:  # Every hour
                customers_in_queue = len(self.queue)
                busy_windows = sum(
                    1 for w in self.service_windows if not w.is_available
                )
                print(
                    f"Time {self.current_time.strftime('%H:%M')} - Queue: {customers_in_queue}, Busy windows: {busy_windows}"
                )

            # Find next event time
            next_event_time = self.get_next_event_time(self.current_time)

            if next_event_time is None or next_event_time >= closing_time:
                # Jump to closing time
                self.current_time = closing_time
                break
            else:
                # Jump to next event
                self.current_time = next_event_time

        # Handle closing time - customers still in queue leave
        self.handle_closing_time(closing_time)

        # Wait for any remaining services to complete (customers already being served)
        max_wait_time = closing_time + timedelta(hours=1)  # Max 1 hour after closing
        while self.current_time < max_wait_time:
            self.process_service_completions(self.current_time)

            # Check if all windows are free
            if all(window.is_available for window in self.service_windows):
                break

            # Find next service completion
            next_event_time = self.get_next_event_time(self.current_time)
            if next_event_time is None:
                break

            self.current_time = min(next_event_time, max_wait_time)

        if verbose:
            print(f"Simulation completed at {self.current_time.strftime('%H:%M')}")

        return self.simulation_state
