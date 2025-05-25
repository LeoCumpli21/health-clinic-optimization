"""
This module implements the Repository interface using a pandas DataFrame as the storage system.
The DataFrameRepo class provides methods to list and filter job posts stored in a DataFrame.
"""

import pandas as pd
from src.interfaces.repository import Repository
from typing import Optional, Dict, Any


class DataFrameRepo(Repository):
    def __init__(self, data: pd.DataFrame):
        """Initializes the DataFrameRepo with a pandas DataFrame.

        Args:
            data (pd.DataFrame): The pandas DataFrame to be used as the repository.
        """
        self.data = data

    def get_data(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Retrieves data from the repository, optionally applying filters.

        Args:
            filters (Optional[Dict[str, Any]]): A dictionary of filters to apply.
                Currently, only "ticket_type" is supported as a filter key.
                If None, all data is returned. Defaults to None.

        Returns:
            pd.DataFrame: A DataFrame containing the filtered data.
        """
        if not filters:
            return self.data
        df = self.data
        if "ticket_type" in filters:
            selected_ticket_type = filters["ticket_type"]
            df = df[df["ticket_type"] == selected_ticket_type]

        return df
