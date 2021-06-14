import csv
import re
import os

import osmium


class ExclusionList:
    excluded_names_csv = os.path.join(
        os.path.dirname(__file__), "exclusion_list/names.csv"
    )
    excluded_brands_csv = os.path.join(
        os.path.dirname(__file__), "exclusion_list/brands.csv"
    )
    excluded_place_names = set()
    excluded_brand_names = set()
    punctuation_regex = re.compile(r"""[\]\[\@\?\!\{\}]+""")

    def __init__(self):
        with open(self.excluded_names_csv, "r") as f:
            reader = csv.reader(f, delimiter=",")
            for row in reader:
                self.excluded_place_names.add(str.lower(row[0]))
        with open(self.excluded_brands_csv, "r") as f:
            reader = csv.reader(f, delimiter=",")
            for row in reader:
                self.excluded_brand_names.add(str.lower(row[0]))

    def check_if_excluded(self, v: osmium.osm.OSMObject) -> (bool, str):
        """True if excluded False if not, with reason"""
        place_name = v.tags.get("name", "") or ""

        # on list of excluded place names
        if place_name.lower() in self.excluded_place_names:
            return True, "excluded_place_names"

        # on list of known brand names
        if place_name.lower() in self.excluded_brand_names:
            return True, "excluded_brand_name"

        # remove military checkpoints and other misc
        if v.tags.get("landuse") == "military" and v.tags.get("military") in {
            "checkpoint",
            "bunker",
            "danger_area",
            "nuclear_explosion_site",
            "barracks",
            "pipeline",
        }:
            return True, "military"

        # remove non-mall shops
        if v.tags.get("shop") and v.tags.get("shop") != "mall":
            return True, "non-mall_shop"

        # drop if only 1 character
        if len(place_name) == 1:
            return True, "single_character"

        # drop where name is all digits
        if place_name.isdigit():
            return True, "all_digits"

        # drop stuff where the name is a bit weird (contains punctuation)
        if self.punctuation_regex.match(place_name):
            return True, "weird"

        return False, None
