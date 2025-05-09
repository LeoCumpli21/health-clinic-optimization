import pandas as pd

from scipy.stats import expon

from src.interfaces.distribution_model import DistributionModel


class ExponentialDistributionScipy(DistributionModel):
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
        params = expon.fit(data, floc=loc)
        return params
