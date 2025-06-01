"""This module provides classes for fitting data to specific distributions using SciPy."""

import pandas as pd

from typing import Dict, Optional, Tuple, Any

from scipy.stats import expon, lognorm

from src.interfaces.distribution_model import DistributionModel


class ExponentialDistributionScipy(DistributionModel):
    """
    Represents an exponential distribution model using SciPy.

    Attributes:
        params (Optional[Dict[str, float]]): Parameters of the distribution.
        distribution: The SciPy exponential distribution object.
    """

    def __init__(self, params: Optional[Dict[str, float]] = None):
        super().__init__()
        self.params = params
        self.distribution = None

    def fit(
        self,
        data: pd.DataFrame,
    ) -> Tuple[Any, ...]:
        """Fits the exponential distribution to the provided data.

        Args:
            data: The data to fit the model to.

        Returns:
            The fitted parameters of the distribution (loc, scale).
        """
        params = expon.fit(data)
        self.params = {"loc": params[0], "scale": params[1]}
        self.distribution = expon(loc=params[0], scale=params[1])
        return params


class LogNormalDistributionScipy(DistributionModel):
    """
    Represents a log-normal distribution model using SciPy.

    Attributes:
        params (Optional[Dict[str, float]]): Parameters of the distribution.
        distribution: The SciPy log-normal distribution object.
    """

    def __init__(self, params: Optional[Dict[str, float]] = None):
        super().__init__()
        self.params = params
        self.distribution = None

    def fit(
        self,
        data: pd.DataFrame,
    ) -> Tuple[Any, ...]:
        """Fits the log-normal distribution to the provided data.

        Args:
            data: The data to fit the model to.

        Returns:
            The fitted parameters of the distribution (shape, loc, scale).
        """
        params = lognorm.fit(data)
        self.params = {"s": params[0], "loc": params[1], "scale": params[2]}
        self.distribution = lognorm(s=params[0], loc=params[1], scale=params[2])
        return params
