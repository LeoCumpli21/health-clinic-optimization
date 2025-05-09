from abc import ABC, abstractmethod

import pandas as pd


class DistributionModel(ABC):
    @abstractmethod
    def fit(self, data: pd.DataFrame):
        """
        Fit the distribution model to the data.
        :param data: The data to fit the model to.
        """
        pass
