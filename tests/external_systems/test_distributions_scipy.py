import pytest
import pandas as pd
import numpy as np  # Added import

from scipy.stats import expon
from scipy.stats import lognorm

from src.external_systems.distributions_scipy import (
    ExponentialDistributionScipy,
    LogNormalDistributionScipy,
)


@pytest.fixture
def exponential_distribution_scipy_instance():
    return ExponentialDistributionScipy()


@pytest.fixture
def lognormal_distribution_scipy_instance():
    """Fixture to create an instance of LogNormalDistributionScipy."""
    return LogNormalDistributionScipy()


def test_exponential_dist_fit_estimates_params_without_fixed_loc(
    exponential_distribution_scipy_instance,
):
    """
    Test that fit estimates loc and scale when loc is not fixed.
    """
    # Generate data from a known exponential distribution
    true_loc = 0.5
    true_scale = 2.0
    sample_data = expon.rvs(loc=true_loc, scale=true_scale, size=1000, random_state=42)
    data_df = pd.DataFrame(sample_data, columns=["values"])

    # Fit the model
    fitted_loc, fitted_scale = exponential_distribution_scipy_instance.fit(
        data_df["values"]
    )

    # Check if the estimated parameters are close to the true parameters
    assert np.isclose(fitted_loc, true_loc, atol=0.1)
    assert np.isclose(fitted_scale, true_scale, atol=0.1)


def test_lognormal_fit_estimates_params(lognormal_distribution_scipy_instance):
    """
    Test that fit correctly estimates the shape, loc, and scale parameters
    of a log-normal distribution.
    """
    # Define true parameters for a log-normal distribution
    true_shape = 0.954  # s parameter for lognorm
    true_loc = 0.1
    true_scale = 1.5

    # Generate random data from this log-normal distribution
    sample_data = lognorm.rvs(
        s=true_shape, loc=true_loc, scale=true_scale, size=2000, random_state=42
    )
    data_df = pd.DataFrame(sample_data, columns=["values"])

    # Fit the LogNormalDistributionScipy model to the generated data
    fitted_shape, fitted_loc, fitted_scale = lognormal_distribution_scipy_instance.fit(
        data_df["values"]
    )

    # Check if the estimated parameters are close to the true parameters
    # Note: Parameter estimation for log-normal can be sensitive, so tolerances might need adjustment.
    assert np.isclose(
        fitted_shape, true_shape, atol=0.1
    ), f"Shape: Expected {true_shape}, Got {fitted_shape}"
    assert np.isclose(
        fitted_loc, true_loc, atol=0.1
    ), f"Loc: Expected {true_loc}, Got {fitted_loc}"
    assert np.isclose(
        fitted_scale, true_scale, atol=0.1
    ), f"Scale: Expected {true_scale}, Got {fitted_scale}"
