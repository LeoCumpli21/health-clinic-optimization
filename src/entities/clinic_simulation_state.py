"""
Defines the ClinicSimulationState class, which tracks the state of the clinic simulation.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from src.entities.customer import Customer


@dataclass
class CustomerRecord:
    """Records a customer's journey through the clinic."""

    customer_id: int
    ticket_type: str
    arrival_time: datetime
    service_start_time: Optional[datetime] = None
    service_end_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    was_served: bool = False
    left_at_closing: bool = False

    @property
    def total_wait_time_minutes(self) -> Optional[float]:
        """Calculate total wait time in minutes."""
        if self.service_start_time is None:
            return None
        return (self.service_start_time - self.arrival_time).total_seconds() / 60.0

    @property
    def service_time_minutes(self) -> Optional[float]:
        """Calculate service time in minutes."""
        if self.service_start_time is None or self.service_end_time is None:
            return None
        return (self.service_end_time - self.service_start_time).total_seconds() / 60.0

    @property
    def total_time_in_clinic_minutes(self) -> Optional[float]:
        """Calculate total time in clinic in minutes."""
        if self.departure_time is None:
            return None
        return (self.departure_time - self.arrival_time).total_seconds() / 60.0


class ClinicSimulationState:
    """Tracks the state and metrics of the clinic simulation."""

    def __init__(self):
        self.customer_records: List[CustomerRecord] = []
        self.current_time: Optional[datetime] = None
        self.simulation_start_time: Optional[datetime] = None
        self.simulation_end_time: Optional[datetime] = None

        # Metrics tracking
        self.total_customers_arrived = 0
        self.total_customers_served = 0
        self.total_customers_left_at_closing = 0

        # Time-based metrics (will be calculated at the end)
        self.avg_wait_time_minutes: Optional[float] = None
        self.avg_service_time_minutes: Optional[float] = None
        self.avg_total_time_minutes: Optional[float] = None
        self.max_wait_time_minutes: Optional[float] = None
        self.customers_waiting_over_20_min: int = 0

    def add_customer_arrival(self, customer: Customer) -> None:
        """Record a customer's arrival."""
        record = CustomerRecord(
            customer_id=customer.customer_id,
            ticket_type=customer.ticket_type,
            arrival_time=customer.arrival_time,
        )
        self.customer_records.append(record)
        self.total_customers_arrived += 1

    def record_service_start(
        self, customer: Customer, service_start_time: datetime
    ) -> None:
        """Record when a customer starts being served."""
        for record in self.customer_records:
            if record.customer_id == customer.customer_id:
                record.service_start_time = service_start_time
                break

    def record_service_completion(
        self, customer: Customer, service_end_time: datetime
    ) -> None:
        """Record when a customer's service is completed."""
        for record in self.customer_records:
            if record.customer_id == customer.customer_id:
                record.service_end_time = service_end_time
                record.departure_time = service_end_time
                record.was_served = True
                self.total_customers_served += 1
                break

    def record_customer_left_at_closing(
        self, customer: Customer, closing_time: datetime
    ) -> None:
        """Record when a customer leaves at closing time without being served."""
        for record in self.customer_records:
            if record.customer_id == customer.customer_id:
                record.departure_time = closing_time
                record.left_at_closing = True
                self.total_customers_left_at_closing += 1
                break

    def calculate_final_metrics(self) -> None:
        """Calculate final simulation metrics."""
        served_customers = [r for r in self.customer_records if r.was_served]

        if served_customers:
            wait_times = [
                r.total_wait_time_minutes
                for r in served_customers
                if r.total_wait_time_minutes is not None
            ]
            service_times = [
                r.service_time_minutes
                for r in served_customers
                if r.service_time_minutes is not None
            ]
            total_times = [
                r.total_time_in_clinic_minutes
                for r in served_customers
                if r.total_time_in_clinic_minutes is not None
            ]

            if wait_times:
                self.avg_wait_time_minutes = sum(wait_times) / len(wait_times)
                self.max_wait_time_minutes = max(wait_times)
                self.customers_waiting_over_20_min = len(
                    [w for w in wait_times if w > 20]
                )

            if service_times:
                self.avg_service_time_minutes = sum(service_times) / len(service_times)

            if total_times:
                self.avg_total_time_minutes = sum(total_times) / len(total_times)

    def get_summary_dict(self) -> Dict[str, Any]:
        """Get a summary of the simulation results as a dictionary."""
        return {
            "simulation_start_time": self.simulation_start_time,
            "simulation_end_time": self.simulation_end_time,
            "total_customers_arrived": self.total_customers_arrived,
            "total_customers_served": self.total_customers_served,
            "total_customers_left_at_closing": self.total_customers_left_at_closing,
            "service_rate_percentage": (
                (self.total_customers_served / self.total_customers_arrived * 100)
                if self.total_customers_arrived > 0
                else 0
            ),
            "avg_wait_time_minutes": self.avg_wait_time_minutes,
            "avg_service_time_minutes": self.avg_service_time_minutes,
            "avg_total_time_minutes": self.avg_total_time_minutes,
            "max_wait_time_minutes": self.max_wait_time_minutes,
            "customers_waiting_over_20_min": self.customers_waiting_over_20_min,
            "percentage_waiting_over_20_min": (
                (self.customers_waiting_over_20_min / self.total_customers_served * 100)
                if self.total_customers_served > 0
                else 0
            ),
        }

    def print_summary(self) -> None:
        """Print a summary of the simulation results."""
        self.calculate_final_metrics()
        summary = self.get_summary_dict()

        print("\n" + "=" * 60)
        print("           CLINIC SIMULATION SUMMARY")
        print("=" * 60)
        print(
            f"Simulation Period: {summary['simulation_start_time']} to {summary['simulation_end_time']}"
        )
        print(f"Total customers arrived: {summary['total_customers_arrived']}")
        print(f"Total customers served: {summary['total_customers_served']}")
        print(
            f"Customers left at closing: {summary['total_customers_left_at_closing']}"
        )
        print(f"Service rate: {summary['service_rate_percentage']:.1f}%")
        print("\n--- TIMING METRICS (for served customers) ---")
        if summary["avg_wait_time_minutes"] is not None:
            print(f"Average wait time: {summary['avg_wait_time_minutes']:.2f} minutes")
            print(f"Maximum wait time: {summary['max_wait_time_minutes']:.2f} minutes")
            print(
                f"Customers waiting > 20 min: {summary['customers_waiting_over_20_min']} ({summary['percentage_waiting_over_20_min']:.1f}%)"
            )
        if summary["avg_service_time_minutes"] is not None:
            print(
                f"Average service time: {summary['avg_service_time_minutes']:.2f} minutes"
            )
        if summary["avg_total_time_minutes"] is not None:
            print(
                f"Average total time in clinic: {summary['avg_total_time_minutes']:.2f} minutes"
            )
        print("=" * 60)
