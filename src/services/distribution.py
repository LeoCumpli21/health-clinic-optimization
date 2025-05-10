import pandas as pd

from src.interfaces.distribution_model import DistributionModel


class Distribution:
    def __init__(self):
        self.distribution = None

    def fit_distribution(self, data: pd.DataFrame, model: DistributionModel):

        params = model.fit(data)
        self.distribution = model.distribution
        return params
