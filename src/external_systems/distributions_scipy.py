import pandas as pd

from typing import Dict, Optional

from scipy.stats import expon, lognorm

from src.interfaces.distribution_model import DistributionModel


class ExponentialDistributionScipy(DistributionModel):
    def __init__(self, params: Optional[Dict[str, float]] = None):
        self.params = params
        self.distribution = None

    def fit(
        self,
        data: pd.DataFrame,
        loc: float | None = None,
    ):
        """
        Fit the exponential distribution to the data.
        If loc is specified, it will be used as a fixed parameter.

        :param data: The data to fit the model to.
        :param loc: The location parameter of the distribution.

        :return: The fitted parameters of the distribution (loc, scale).
        """
        params = expon.fit(data)
        self.distribution = expon(loc=params[0], scale=params[1])
        return params


class LogNormalDistributionScipy(DistributionModel):
    def __init__(self, params: Optional[Dict[str, float]] = None):
        self.params = params
        self.distribution = None

    def fit(
        self,
        data: pd.DataFrame,
    ):
        """
        Fit the log-normal distribution to the data.

        :param data: The data to fit the model to.

        :return: The fitted parameters of the distribution (shape, loc, scale).
        """
        params = lognorm.fit(data)
        self.distribution = lognorm(s=params[0], loc=params[1], scale=params[2])
        return params
