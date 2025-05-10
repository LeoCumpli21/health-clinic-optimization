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


def test_exponential_dist_fit_uses_fixed_loc_and_estimates_scale(
    exponential_distribution_scipy_instance,
):
    """
    Test that fit uses the fixed loc and estimates scale.
    """
    # Generate data from a known exponential distribution
    actual_data_loc = 0.5  # Loc used for data generation
    actual_data_scale = 2.0  # Scale used for data generation
    fixed_loc_param = 0.2  # Loc to be fixed during fitting

    sample_data = expon.rvs(
        loc=actual_data_loc, scale=actual_data_scale, size=1000, random_state=42
    )
    data_df = pd.DataFrame(sample_data, columns=["values"])

    # Fit the model with a fixed loc
    # Note: scipy's expon.fit with floc will try to fit the scale given that loc.
    # The estimated scale will be relative to the fixed loc.
    fitted_loc, fitted_scale = exponential_distribution_scipy_instance.fit(
        data_df["values"], loc=fixed_loc_param
    )

    # Check if the returned loc is the same as the fixed loc
    assert fitted_loc == fixed_loc_param

    # To verify the scale, we need to understand what `expon.fit` does with `floc`.
    # It fits `data - floc` to an exponential distribution with loc=0.
    # So, the scale parameter would be the mean of `(data - floc)` for data > floc.
    # Let's calculate the expected scale manually for verification.
    # This is a more complex assertion because the true underlying distribution has a different loc.
    # For simplicity here, we'll just check that a scale is returned and it's positive.
    # A more rigorous check would involve comparing against `expon.fit(data_df['values'] - fixed_loc_param, floc=0)[1]`
    # or `expon.fit(data_df['values'], floc=fixed_loc_param)[1]`

    # For this test, we'll check that the fitted_loc is indeed the fixed_loc_param
    # and that the scale is a positive number (as scale must be > 0).
    assert fitted_scale > 0

    # A more precise check for scale if data was generated with fixed_loc_param:
    if actual_data_loc == fixed_loc_param:
        # If data was generated with the same loc we are fixing, scale should be close
        assert np.isclose(fitted_scale, actual_data_scale, atol=0.1)
    else:
        # If data loc is different from fixed loc, the estimated scale will be different.
        # We can check it's reasonably estimated.
        # For example, by fitting directly with scipy and comparing
        _, expected_scipy_scale = expon.fit(data_df["values"], floc=fixed_loc_param)
        assert np.isclose(fitted_scale, expected_scipy_scale, atol=1e-9)


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
