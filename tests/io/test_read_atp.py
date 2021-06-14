import os

import pytest
import pandas as pd
from numpy import nan

from osm_commercial.io import read_atp

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class TestReadATP:
    filepath = os.path.join(DATA_DIR, "mock_data.geojson")

    def test_load_file(self):
        df = read_atp.read_source(self.filepath)

        assert "latitude" in df.columns
        assert "longitude" in df.columns
        assert len(df.index) == 15
        assert pd.api.types.is_string_dtype(df["addr:postcode"])

    @pytest.mark.parametrize(
        "input_value,expected_value",
        [
            # some bad values that should get cleaned
            (" ", nan),
            ("     ", nan),
            ("", nan),
            # some good values that should stay the same
            ("good value", "good value"),
            (1.0, 1.0),
        ],
    )
    def test_cleanup_data(self, input_value, expected_value):
        mock_data = pd.DataFrame(data=[input_value], columns=["value"], index=[0])

        cleaned = read_atp.cleanup_data(mock_data)
        expected = pd.DataFrame(data=[expected_value], columns=["value"], index=[0])
        assert pd.testing.assert_frame_equal(cleaned, expected) is None
