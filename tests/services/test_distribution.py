import pytest
from unittest import mock
from src.services.distribution import Distribution

import pandas as pd


@pytest.fixture
def exponential_dist_params():
    return [0, 1]  # loc, scale


def test_fit_distribution_with_parameters(exponential_dist_params):
    model = mock.Mock()
    model.fit.return_value = exponential_dist_params
    data = pd.DataFrame()
    distribution_model = Distribution()
    returned_params = distribution_model.fit_distribution(data, model)
    assert returned_params == exponential_dist_params
