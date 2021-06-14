import getpass
import glob
import logging
import os
import typing

import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DataError

from osm_commercial.io.database import GeoDB
from osm_commercial.io.read_atp import read_source, SourceReadError


# sources we just don't care about and are really noisy
SOURCES_TO_IGNORE = {"usps_collection_boxes"}


def conform_schema(
    df: pd.DataFrame, valid_column_names: typing.List[str]
) -> pd.DataFrame:
    """Update column names:
    - replace colons with underscores
    - rename for clarity
    - drop any columns that don't exist in the table schema
    """
    col_map = {x: x.replace(":", "_") for x in df.columns}
    col_map["brand:wikidata"] = "wikidata_id"

    df.rename(columns=col_map, inplace=True)
    df.drop(columns=list(set(df.columns) - set(valid_column_names)), inplace=True)

    return df


def set_modified_by(df: pd.DataFrame, user: str) -> pd.DataFrame:
    """Set modified_by value"""
    df["modified_by"] = user
    return df


def load_source(
    geojson_file: str,
    con: Engine,
    target_table: str,
    valid_column_names: typing.List[str],
):
    """Load an alltheplaces geojson file to the target table"""
    try:
        df = read_source(geojson_file)
    except SourceReadError:
        logging.warning("Empty file: {}".format(geojson_file))  # TODO
        return

    df = conform_schema(df, valid_column_names=valid_column_names)
    df = set_modified_by(df, user=USER)
    try:
        df.to_sql(con=con, name=target_table, if_exists="append", index=False)
    except DataError:
        logging.warning("Unable to load file: {}".format(geojson_file))
        return


def main(db: GeoDB, directory: str, target_table: str):
    """Load all geojson files from directory to database then create geometry and spatial index"""
    column_names = [c.name for c in db.base.classes.alltheplaces.__table__.columns]

    for f in glob.glob(f"{directory}/*.geojson"):
        if os.path.splitext(os.path.basename(f))[0] in SOURCES_TO_IGNORE:
            continue
        load_source(
            f, db.engine, target_table=target_table, valid_column_names=column_names
        )

    # after all loaded, create point geom and index
    with db.engine.connect() as con:
        con.execute(
            """UPDATE alltheplaces SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);"""
        )
        con.execute(
            """CREATE INDEX geom_alltheplaces_idx ON alltheplaces USING GIST (geom);"""
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Load all valid alltheplaces geojson files to database"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="data/alltheplaces/output",
        help="Directory containing alltheplaces output geojson files",
    )
    parser.add_argument("--host", default="localhost", help="postgresql host")
    parser.add_argument("--port", default=5432, help="postgresql port")
    parser.add_argument("--user", default=getpass.getuser(), help="postgresql username")
    parser.add_argument("--password", default=None, help="postgresql password")
    parser.add_argument(
        "--database", default="osm_commercial", help="postgresql database"
    )
    parser.add_argument(
        "--table", default="alltheplaces", help="postgresql table to load to"
    )
    parser.add_argument(
        "--debug", default=False, action="store_true", help="Run in debug mode"
    )
    parser.add_argument(
        "--echo", default=False, action="store_true", help="Echo database statements"
    )

    args = parser.parse_args()
    DEBUG = args.debug
    USER = args.user

    logging.basicConfig(
        filename="alltheplaces.log",
        level=logging.DEBUG if DEBUG else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    db = GeoDB(
        host=args.host,
        port=args.port,
        username=args.user,
        password=args.password,
        database=args.database,
        echo=args.echo,
    )
    db.test_connection()

    main(db=db, directory=args.directory, target_table=args.table)
