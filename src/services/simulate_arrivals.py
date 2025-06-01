"""Simulates patient arrivals for a health clinic using Non-Homogeneous Poisson Processes.

This module provides functions to simulate arrival times based on historical
arrival rate data. It includes utilities for:
- Calculating the maximum arrival rate (lambda_max) for a given location and group.
- Retrieving the specific arrival rate (lambda(t)) for a given time.
- Simulating arrival times using the thinning algorithm for NHPP.
- Analyzing and plotting the simulated arrivals against actual rates.
- Orchestrating the entire simulation process.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List
from collections import Counter


def calculate_lambda_max(rates_df: pd.DataFrame, sucursal: str, group: str) -> float:
    """Calculates the maximum arrival rate (lambda_max) for a given sucursal and group.

    This function filters the provided DataFrame of arrival rates for a specific
    'Sucursal' (branch/location) and 'Group' (customer type). It then
    determines the highest 'ArrivalRate_Lambda_t' (arrivals per hour)
    among these filtered rates. This maximum rate is crucial for the thinning
    algorithm used in Non-Homogeneous Poisson Process (NHPP) simulation,
    as it serves as the upper bound for the variable arrival rate lambda(t).

    Args:
        rates_df: A pandas DataFrame containing historical arrival rates.
            Expected columns include 'Sucursal', 'Group', and
            'ArrivalRate_Lambda_t'.
        sucursal: The specific sucursal (e.g., 'Sucursal A') to filter by.
        group: The specific customer group (e.g., 'Priority Patients') to
            filter by.

    Returns:
        The maximum arrival rate (lambda_max) found for the specified
        sucursal and group. Returns 0.0 if no rates are found for the
        given combination, along with a warning message.
    """
    current_rates = rates_df[
        (rates_df["Sucursal"] == sucursal) & (rates_df["Group"] == group)
    ]["ArrivalRate_Lambda_t"]

    if current_rates.empty:
        print(
            f"Warning: No rates found for {sucursal}, {group}. Setting lambda_max to 0."
        )
        return 0.0

    lambda_max_val = current_rates.max()
    print(
        f"For {sucursal} - Group {group}, calculated λ_max = {lambda_max_val:.4f} arrivals/hour"
    )
    return lambda_max_val


def get_lambda_for_time(
    time_val: pd.Timestamp, rates_df: pd.DataFrame, sucursal: str, group: str
) -> float:
    """Retrieves the arrival rate lambda(t) for a specific time, sucursal, and group.

    This function looks up the arrival rate in the `rates_df` that corresponds
    to the provided `time_val` (timestamp), `sucursal`, and `group`. It matches
    based on the day of the week and hour of the day extracted from `time_val`.
    This rate, lambda(t), represents the expected number of arrivals per hour
    at that specific time and is used in the NHPP simulation to determine the
    probability of accepting a potential arrival.

    Args:
        time_val: The specific pandas Timestamp for which to retrieve the
            arrival rate.
        rates_df: A pandas DataFrame containing arrival rates. Expected columns
            include 'Sucursal', 'Group', 'DayOfWeekName', 'HourOfDay', and
            'ArrivalRate_Lambda_t'.
        sucursal: The sucursal of interest.
        group: The group of interest.

    Returns:
        The arrival rate (lambda(t)) for the given time, sucursal, and group.
        Returns 0.0 if no specific rate entry is found in `rates_df` for the
        given criteria.
    """
    day_of_week = time_val.strftime("%A")
    hour_of_day = time_val.hour

    rate_entry = rates_df[
        (rates_df["Sucursal"] == sucursal)
        & (rates_df["Group"] == group)
        & (rates_df["DayOfWeekName"] == day_of_week)
        & (rates_df["HourOfDay"] == hour_of_day)
    ]

    if not rate_entry.empty:
        return rate_entry["ArrivalRate_Lambda_t"].iloc[0]
    return 0.0


def simulate_nhpp_arrivals(
    rates_df: pd.DataFrame,
    sucursal: str,
    group: str,
    lambda_max: float,
    simulation_start_dt: pd.Timestamp,
    simulation_duration_hours: int,
) -> List[pd.Timestamp]:
    """Simulates arrival times using a Non-Homogeneous Poisson Process (NHPP).

    This function implements the thinning (or acceptance-rejection) algorithm
    to generate arrival times that follow a time-varying Poisson process.
    It first generates potential arrival times from a homogeneous Poisson
    process with rate `lambda_max`. Then, each potential arrival at time t*
    is "thinned" (accepted) with probability lambda(t*)/lambda_max, where
    lambda(t*) is the actual arrival rate at that time.

    The simulation proceeds hour by hour for the specified duration.

    Args:
        rates_df: DataFrame with historical arrival rates, used by
            `get_lambda_for_time` to find lambda(t*).
        sucursal: The sucursal for which to simulate arrivals.
        group: The customer group for which to simulate arrivals.
        lambda_max: The maximum arrival rate, pre-calculated by
            `calculate_lambda_max`. Must be positive.
        simulation_start_dt: A pandas Timestamp indicating when the
            simulation period begins.
        simulation_duration_hours: The total number of hours the simulation
            should run for.

    Returns:
        A list of pandas Timestamps, where each timestamp represents a
        simulated arrival time. Returns an empty list if `lambda_max` is not
        positive.
    """
    if lambda_max <= 0:
        print(
            f"Cannot simulate for {sucursal} - Group {group} as lambda_max ({lambda_max}) is not positive."
        )
        return []

    nhpp_arrivals: List[pd.Timestamp] = []
    current_datetime = simulation_start_dt
    simulation_end_dt = simulation_start_dt + pd.Timedelta(
        hours=simulation_duration_hours
    )

    print(
        f"Starting NHPP simulation for {simulation_duration_hours} hours from {simulation_start_dt.strftime('%Y-%m-%d %H:%M')}..."
    )

    while current_datetime < simulation_end_dt:
        inter_arrival_time_hours = np.random.exponential(1.0 / lambda_max)
        potential_arrival_datetime = current_datetime + pd.Timedelta(
            hours=inter_arrival_time_hours
        )

        if potential_arrival_datetime >= simulation_end_dt:
            break

        current_datetime = potential_arrival_datetime
        lambda_at_t_star = get_lambda_for_time(
            current_datetime, rates_df, sucursal, group
        )

        if lambda_max == 0:  # Should be caught earlier, but as a safeguard
            acceptance_probability = 0
        else:
            acceptance_probability = lambda_at_t_star / lambda_max

        if np.random.uniform(0, 1) < acceptance_probability:
            nhpp_arrivals.append(current_datetime)

    print(
        f"Generated {len(nhpp_arrivals)} arrivals for {sucursal} - Group {group} over {simulation_duration_hours / 24:.1f} days."
    )
    return nhpp_arrivals


def _get_day_of_week_simulation_counts(
    sim_start_dt: pd.Timestamp, sim_duration_days: int
) -> Counter:
    """Counts occurrences of each day of the week within a simulation period.

    This helper function iterates through each day of the simulation period,
    starting from `sim_start_dt` for `sim_duration_days`, and counts how
    many times each day of the week (e.g., Monday, Tuesday) occurs.
    This is used for normalizing simulated arrival counts when comparing
    against average actual rates.

    Args:
        sim_start_dt: The pandas Timestamp marking the beginning of the
            simulation period.
        sim_duration_days: The total duration of the simulation in days.

    Returns:
        A collections.Counter object mapping day names (e.g., "Monday")
        to their frequency within the simulation period.
    """
    day_names_in_period = []
    for i in range(sim_duration_days):
        current_day = sim_start_dt + pd.Timedelta(days=i)
        day_names_in_period.append(current_day.strftime("%A"))
    return Counter(day_names_in_period)


def analyze_and_plot_simulation_results(
    simulated_arrivals_list: List[pd.Timestamp],
    sucursal: str,
    group: str,
    all_rates_df: pd.DataFrame,
    simulation_start_dt: pd.Timestamp,
    simulation_duration_days: int,
    to_plot: bool = False,
) -> pd.DataFrame:
    """Analyzes simulated arrivals and optionally plots them against actual rates.

    This function takes a list of simulated arrival timestamps, converts them
    into a DataFrame, and performs an analysis. It calculates the average
    number of simulated arrivals per hour for each day of the week.
    If `to_plot` is True, it generates a series of subplots (one for each
    day of the week) comparing these simulated hourly averages against the
    actual average hourly arrival rates obtained from `all_rates_df`.

    The analysis involves:
    1. Converting the list of arrival timestamps to a DataFrame.
    2. Extracting 'DayOfWeekName' and 'HourOfDay' from timestamps.
    3. Counting how many times each day of the week was part of the simulation
       (using `_get_day_of_week_simulation_counts`) for normalization.
    4. For each day of the week:
        a. Grouping simulated arrivals by hour and calculating total counts.
        b. Normalizing these counts by the number of times that day was simulated
           to get an average hourly arrival rate.
        c. Retrieving actual average hourly rates from `all_rates_df`.
        d. If `to_plot` is True, plotting both simulated and actual rates on a subplot.

    Args:
        simulated_arrivals_list: A list of pandas Timestamps representing
            the simulated arrival times.
        sucursal: The sucursal for which the simulation was run.
        group: The customer group for which the simulation was run.
        all_rates_df: A pandas DataFrame containing the actual historical
            arrival rates, used for comparison. Expected columns include
            'Sucursal', 'Group', 'DayOfWeekName', 'HourOfDay', and
            'ArrivalRate_Lambda_t'.
        simulation_start_dt: The pandas Timestamp when the simulation began.
            Used for context in plots and for `_get_day_of_week_simulation_counts`.
        simulation_duration_days: The total duration of the simulation in days.
            Used for normalization and plot context.
        to_plot: A boolean indicating whether to generate and display plots.
            Defaults to False.

    Returns:
        A pandas DataFrame containing the simulated arrival data, augmented with
        'Sucursal', 'Group', 'DayOfWeekName', and 'HourOfDay'. Returns an
        empty DataFrame if `simulated_arrivals_list` is empty.
    """
    if not simulated_arrivals_list:
        print(
            f"No simulated arrivals for {sucursal} - Group {group} to analyze or plot."
        )
        return pd.DataFrame()

    sim_arrivals_df = pd.DataFrame(
        {"SimulatedTurnoInicioDateTime": simulated_arrivals_list}
    )
    sim_arrivals_df["Sucursal"] = sucursal
    sim_arrivals_df["Group"] = group

    print("\nFirst 5 simulated arrival times:")
    print(sim_arrivals_df.head())

    sim_arrivals_df["DayOfWeekName"] = sim_arrivals_df[
        "SimulatedTurnoInicioDateTime"
    ].dt.strftime("%A")
    sim_arrivals_df["HourOfDay"] = sim_arrivals_df[
        "SimulatedTurnoInicioDateTime"
    ].dt.hour

    # Get counts of how many times each day of the week was simulated
    day_occurrences = _get_day_of_week_simulation_counts(
        simulation_start_dt, simulation_duration_days
    )

    days_of_week_ordered = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    if to_plot:
        fig, axes = plt.subplots(
            nrows=len(days_of_week_ordered), ncols=1, figsize=(12, 24), sharex=True
        )  # Adjusted figsize
        fig.suptitle(
            f'Daily Comparison: Avg. Hourly Arrivals for {sucursal}-{group}\nSimulation over {simulation_duration_days} days starting {simulation_start_dt.strftime("%Y-%m-%d")}',
            fontsize=16,
        )

        for i, day_name in enumerate(days_of_week_ordered):
            ax = axes[i]

            # Simulated data for this day of the week
            sim_daily_df = sim_arrivals_df[sim_arrivals_df["DayOfWeekName"] == day_name]
            sim_hourly_total_counts_for_day = sim_daily_df.groupby("HourOfDay").size()

            num_times_this_day_simulated = day_occurrences.get(day_name, 0)

            if num_times_this_day_simulated > 0:
                avg_sim_hourly_counts_for_day = (
                    sim_hourly_total_counts_for_day / num_times_this_day_simulated
                )
            else:
                avg_sim_hourly_counts_for_day = pd.Series(
                    dtype=float
                )  # Empty if day wasn't in sim
                if (
                    not sim_hourly_total_counts_for_day.empty
                ):  # Should not happen if num_times_this_day_simulated is 0
                    print(
                        f"Warning: Data found for {day_name} but it was not expected in simulation period."
                    )

            avg_sim_hourly_counts_for_day.reindex(np.arange(0, 24), fill_value=0).plot(
                ax=ax,
                kind="line",
                label="Avg. Simulated Arrivals/Hour",
                marker="x",
                drawstyle="steps-post",
            )

            # Actual data for this day of the week
            actual_rates_for_day = all_rates_df[
                (all_rates_df["Sucursal"] == sucursal)
                & (all_rates_df["Group"] == group)
                & (all_rates_df["DayOfWeekName"] == day_name)
            ]

            if not actual_rates_for_day.empty:
                actual_hourly_avg_rates_for_day = actual_rates_for_day.groupby(
                    "HourOfDay"
                )["ArrivalRate_Lambda_t"].mean()
                actual_hourly_avg_rates_for_day.reindex(
                    np.arange(0, 24), fill_value=0
                ).plot(
                    ax=ax,
                    kind="line",
                    label=f"Avg. Actual λ(t)",
                    marker="o",
                    linestyle="--",
                    drawstyle="steps-post",
                )
            else:
                ax.plot(
                    [],
                    [],
                    label=f"Avg. Actual λ(t) (No data)",
                    marker="o",
                    linestyle="--",
                )

            ax.set_title(day_name)
            ax.set_ylabel("Avg. Arrivals / Hour")
            ax.legend()
            ax.grid(True, which="both", linestyle=":", linewidth=0.7)
            ax.set_xticks(np.arange(0, 24, 1))

        axes[-1].set_xlabel("Hour of Day")  # Set x-label only on the last subplot
        plt.tight_layout(
            rect=(0.0, 0.03, 1.0, 0.97)
        )  # Adjust layout to make space for suptitle
        plt.show()

    return sim_arrivals_df


def run_arrival_simulation(
    full_arrival_rates_df: pd.DataFrame,
    sucursal_to_simulate: str,
    group_to_simulate: str,
    sim_start_datetime_str: str,
    sim_duration_days: int,
) -> pd.DataFrame:
    """Orchestrates the NHPP arrival simulation and analysis.

    This function serves as the main entry point to run a complete arrival
    simulation for a specific sucursal and group. It performs the following steps:
    1. Validates that `full_arrival_rates_df` contains all required columns.
    2. Converts `sim_start_datetime_str` to a pandas Timestamp object and
       validates `sim_duration_days`.
    3. Calculates `lambda_max` using `calculate_lambda_max`. If `lambda_max`
       is not positive, the simulation is halted.
    4. Simulates arrival times using `simulate_nhpp_arrivals`.
    5. Analyzes the simulated arrivals and optionally plots them against actual
       rates using `analyze_and_plot_simulation_results`. The plotting behavior
       within `analyze_and_plot_simulation_results` is controlled by its
       `to_plot` parameter (which defaults to False but could be modified or
       exposed here if needed). Currently, it plots by default if `to_plot` is True.

    Args:
        full_arrival_rates_df: The primary pandas DataFrame containing all
            historical arrival rate data. Expected columns: 'Sucursal', 'Group',
            'DayOfWeekName', 'HourOfDay', 'ArrivalRate_Lambda_t'.
        sucursal_to_simulate: The name of the sucursal for which to run the
            simulation.
        group_to_simulate: The name of the customer group for which to run
            the simulation.
        sim_start_datetime_str: A string representing the start date and time
            for the simulation (e.g., "2023-01-01 00:00:00").
        sim_duration_days: The total number of days the simulation should cover.
            Must be a positive integer.

    Returns:
        A pandas DataFrame containing the detailed simulated arrival data,
        as returned by `analyze_and_plot_simulation_results`. Returns an empty
        DataFrame if critical errors occur (e.g., missing columns, invalid
        date string, non-positive simulation duration, or non-positive
        lambda_max).
    """
    required_cols = [
        "Sucursal",
        "Group",
        "DayOfWeekName",
        "HourOfDay",
        "ArrivalRate_Lambda_t",
    ]
    if not all(col in full_arrival_rates_df.columns for col in required_cols):
        missing_cols = [
            col for col in required_cols if col not in full_arrival_rates_df.columns
        ]
        print(f"Error: Input DataFrame is missing required columns: {missing_cols}")
        return pd.DataFrame()

    try:
        simulation_start_dt_obj = pd.Timestamp(sim_start_datetime_str)
    except ValueError as e:
        print(
            f"Error: Invalid sim_start_datetime_str '{sim_start_datetime_str}'. Details: {e}"
        )
        return pd.DataFrame()

    if sim_duration_days <= 0:
        print(
            f"Error: sim_duration_days must be positive. Received: {sim_duration_days}"
        )
        return pd.DataFrame()
    simulation_duration_hours = sim_duration_days * 24

    lambda_max = calculate_lambda_max(
        full_arrival_rates_df, sucursal_to_simulate, group_to_simulate
    )
    if lambda_max <= 0:  # Also handles case where lambda_max might be calculated as 0
        print(
            f"Halting simulation for {sucursal_to_simulate} - {group_to_simulate} due to non-positive or zero lambda_max ({lambda_max})."
        )
        return pd.DataFrame()

    simulated_arrivals = simulate_nhpp_arrivals(
        rates_df=full_arrival_rates_df,
        sucursal=sucursal_to_simulate,
        group=group_to_simulate,
        lambda_max=lambda_max,
        simulation_start_dt=simulation_start_dt_obj,  # Pass Timestamp object
        simulation_duration_hours=simulation_duration_hours,
    )

    simulated_arrivals_df = analyze_and_plot_simulation_results(
        simulated_arrivals_list=simulated_arrivals,
        sucursal=sucursal_to_simulate,
        group=group_to_simulate,
        all_rates_df=full_arrival_rates_df,
        simulation_start_dt=simulation_start_dt_obj,  # Pass Timestamp object
        simulation_duration_days=sim_duration_days,
    )

    return simulated_arrivals_df
