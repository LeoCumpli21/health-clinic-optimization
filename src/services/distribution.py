import pandas as pd

from src.interfaces.distribution_model import DistributionModel


class Distribution:
    def __init__(self):
        pass

    def fit_distribution(self, data: pd.DataFrame, model: DistributionModel):

        params = model.fit(data)
        return params
