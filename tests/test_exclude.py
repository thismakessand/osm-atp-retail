from collections import namedtuple
import os
from unittest import mock

import pytest

from osm_commercial.exclude import ExclusionList


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

MockOSMObject = namedtuple("OSMObject", ["tags"])


@pytest.fixture(scope="module")
def exclusion_list():
    mock_open = mock.mock_open()
    with mock.patch("builtins.open", mock_open):
        ExclusionList.excluded_brand_names = {"abc", "abc2"}
        ExclusionList.excluded_place_names = {"area 51"}

    return ExclusionList()


class TestExclusionList:
    @pytest.mark.parametrize(
        "tags,expected_excluded,excluded_reason",
        [
            # some bad values that should get excluded
            ({"name": "abc"}, True, "excluded_brand_name"),
            ({"name": "abc2"}, True, "excluded_brand_name"),
            # not case sensitive
            ({"name": "ABC"}, True, "excluded_brand_name"),
            # excluded by place name
            ({"name": "Area 51"}, True, "excluded_place_names"),
            # excluded by tag value
            ({"landuse": "military", "military": "danger_area"}, True, "military"),
            # excluded short names
            ({"name": "A"}, True, "single_character"),
            # excluded all digit names
            ({"name": "123"}, True, "all_digits"),
            # excluded weird stuff
            ({"name": "!!!"}, True, "weird"),
            # good stuff not excluded
            ({"name": "something good"}, False, None),
            # no name still okay
            ({"name": None}, False, None),
        ],
    )
    def test_check_if_excluded(
        self, exclusion_list, tags, expected_excluded, excluded_reason
    ):
        mock_object = MockOSMObject(tags=tags)

        is_excluded, reason = exclusion_list.check_if_excluded(mock_object)
        assert is_excluded == expected_excluded
        assert reason == excluded_reason
