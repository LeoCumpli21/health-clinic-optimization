"""
This module implements the Repository interface using a pandas DataFrame as the storage system.
The DataFrameRepo class provides methods to list and filter job posts stored in a DataFrame.
"""

import pandas as pd
from src.interfaces.repository import Repository
from typing import Optional, Dict, Any


class DataFrameRepo(Repository):
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def get_data(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:

        if not filters:
            return self.data
        df = self.data
        if "ticket_type" in filters:
            selected_ticket_type = filters["ticket_type"]
            df = df[df["ticket_type"] == selected_ticket_type]

        return df
