import pandas as pd


def get_arrival_rates(sd_data: pd.DataFrame) -> pd.DataFrame:
    # copy dataframe to perform arrivals simulation
    arrivals_simul_df = sd_data.copy()
    # Assuming clinics_df is loaded and has 'Sucursal', 'Group', 'TurnoInicioDateTime'
    # Extract time features
    arrivals_simul_df["Date"] = arrivals_simul_df[
        "TurnoInicioDateTime"
    ].dt.date  # For counting unique days of operation

    # Calculate the number of unique days each specific (Sucursal, Group, DayOfWeek, Hour) slot was observed
    # This is important for averaging correctly.
    # First, count how many distinct dates of operation exist for each Sucursal-Group-DayOfWeek-Hour combination.

    # To count the number of observation periods for each slot:
    # e.g., how many Mondays at 9 AM did we observe for Sucursal A, Group P?
    observation_periods = (
        arrivals_simul_df.groupby(["Sucursal", "Group", "DayOfWeekName", "HourOfDay"])[
            "Date"
        ]
        .nunique()
        .reset_index(name="NumObservationPeriods")
    )

    # Calculate total arrivals for each slot
    total_arrivals_in_slot = (
        arrivals_simul_df.groupby(["Sucursal", "Group", "DayOfWeekName", "HourOfDay"])
        .size()
        .reset_index(name="TotalArrivals")
    )

    # Merge to calculate average rate
    lambda_t_df = pd.merge(
        total_arrivals_in_slot,
        observation_periods,
        on=["Sucursal", "Group", "DayOfWeekName", "HourOfDay"],
    )

    # The rate lambda(t) is arrivals per hour for that slot
    lambda_t_df["ArrivalRate_Lambda_t"] = (
        lambda_t_df["TotalArrivals"] / lambda_t_df["NumObservationPeriods"]
    )

    # You can now sort this for easier lookup or plotting
    days_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    lambda_t_df["DayOfWeekName"] = pd.Categorical(
        lambda_t_df["DayOfWeekName"], categories=days_order, ordered=True
    )
    lambda_t_df.sort_values(
        by=["Sucursal", "Group", "DayOfWeekName", "HourOfDay"], inplace=True
    )
    return lambda_t_df
