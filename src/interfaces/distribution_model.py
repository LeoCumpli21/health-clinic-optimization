from abc import ABC, abstractmethod
from typing import Any, Tuple

import pandas as pd


class DistributionModel(ABC):
    def __init__(self):
        """Initializes the DistributionModel."""
        self.distribution = None

    @abstractmethod
    def fit(self, data: pd.DataFrame) -> Tuple[Any, ...]:
        """Fits the distribution model to the provided data.

        Args:
            data (pd.DataFrame): The input data to fit the model to.

        Returns:
            Tuple[Any, ...]: A tuple containing the fitted distribution parameters
                             or other relevant fitting results.
        """
        pass
