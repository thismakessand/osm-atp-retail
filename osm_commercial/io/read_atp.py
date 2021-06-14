import json

import pandas as pd
from numpy import nan


class SourceReadError(Exception):
    pass


def extract_properties(feature: dict) -> dict:
    """Extract properties from geojson"""
    properties = feature["properties"]

    if "addr:postcode" in properties:
        properties["addr:postcode"] = str(properties["addr:postcode"])

    try:
        geom = feature["geometry"]
    except KeyError:
        return properties

    properties["longitude"], properties["latitude"] = geom["coordinates"]

    return properties


def read_source(geojson: str) -> pd.DataFrame:
    """Convert an alltheplaces geojson file to dataframe"""
    with open(geojson, "r") as json_file:
        try:
            data = json.load(json_file)
        except json.JSONDecodeError:
            raise SourceReadError

    df = pd.DataFrame([extract_properties(x) for x in data["features"]])
    df = cleanup_data(df)
    return df


def cleanup_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up some empty/null values"""
    df = df.replace(r"^\s+$", nan, regex=True)
    df = df.replace("", nan, regex=True)
    return df
