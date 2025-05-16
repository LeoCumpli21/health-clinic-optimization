import pytest

import pandas as pd

from src.external_systems.dataframe_repo import DataFrameRepo


@pytest.fixture
def sample_data():
    data = {"ticket_type": ["P", "N", "C", "F"], "service_time": [2, 3.1, 3.2, 3.3]}
    return pd.DataFrame(data)


def test_repo_get_data_without_parameters(sample_data):
    df_repo = DataFrameRepo(sample_data)
    data_expected = sample_data
    data_result = df_repo.get_data()
    pd.testing.assert_frame_equal(data_result, data_expected)


def test_repo_get_data_with_parameters(sample_data):
    df_repo = DataFrameRepo(sample_data)
    filters = {"ticket_type": "P"}
    data_expected = sample_data[sample_data["ticket_type"] == "P"]
    data_result = df_repo.get_data(filters)
    pd.testing.assert_frame_equal(data_result, data_expected)
