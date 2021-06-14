from collections import OrderedDict
import getpass
import logging
import typing

import osmium
import shapely.wkb as wkblib

from geoalchemy2 import shape
from sqlalchemy.orm import Session, decl_api

from osm_commercial.exclude import ExclusionList
from osm_commercial.io.database import GeoDB


# tags we are interested in, in order of most-specific-to-least-specific
TAGS = OrderedDict(
    {
        "amenity": {
            "marketplace",
            "community_centre",
            "hospital",
            "college",
            "university",
            "prison",
            "library",
        },
        "aeroway": {"aerodrome"},
        "leisure": {"stadium", "sports_centre"},
        "tourism": {"hotel", "museum"},
        "shop": {"mall"},
        "landuse": {"commercial", "retail", "military"},
    }
)


class OsmDB(GeoDB):
    """
    Using SQLAlchemy ORM to do inserts - table already exists
    so we "reflect" the existing database to get the class
    associated with the table.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.CommercialArea = self.base.classes.commercial_area


class PlaceHandler(osmium.SimpleHandler):
    wkbfab = osmium.geom.WKBFactory()

    places = list()
    excluded = list()

    def __init__(self, table_obj: decl_api.DeclarativeMeta, session: Session):
        """Handle features from osm extract"""
        super().__init__()
        self.CommercialArea = table_obj
        self.excluder = ExclusionList()
        self.session = session

    def is_excluded(self, f: osmium.osm.OSMObject) -> bool:
        """Weed out bad data. Run place tags against some rules to see if it should be excluded from insert."""
        is_excluded, excluded_reason = self.excluder.check_if_excluded(f)
        if is_excluded:
            if DEBUG:
                self.excluded.append(
                    (excluded_reason, f.tags.get("name", ""), dict(f.tags))
                )
            return True
        return False

    def classify(self, f: osmium.osm.OSMObject) -> typing.Union[str, None]:
        """Classify the "type" of place, eg marketplace, mall, commercial, etc based on hierarchy of tags
        defined above. Since many places will have multiple matching tags, pick the most specific one to use as the
        place type. If place should be dropped/excluded for quality reasons, return None"""
        for tag, values in TAGS.items():
            if f.tags.get(tag) in values:
                if not self.is_excluded(f):
                    place_type = f.tags[tag]
                    return place_type
                else:
                    return None

        return None

    def area(self, a: osmium.osm.Area):
        """Handler for OSM areas (closed ways/relations with closed ways) features"""
        source_id = f"way/{a.orig_id()}"
        place_type = self.classify(a)

        if place_type:
            try:
                wkb = self.wkbfab.create_multipolygon(a)
            except Exception as e:
                logging.warning(
                    f"Failed to create multipolygon on {a.orig_id()}: {str(e)}"
                )
                return
            poly = wkblib.loads(wkb, hex=True)

            place = self.CommercialArea(
                name=a.tags.get("name"),
                source="osm",
                source_id=source_id,
                place_type=place_type,
                city=a.tags.get("addr:city"),
                admin1=a.tags.get("addr:state") or a.tags.get("addr:province"),
                postal_code=a.tags.get("addr:postcode"),
                country=a.tags.get("addr:country"),
                modified_by=USER,
                geom=shape.from_shape(poly, srid=4326),
            )

            self._add_place(place)

    def _add_place(self, place, insert_batch_size: int = 1000):
        """Add a place; insert to database every 1000 rows"""
        self.places.append(place)

        if len(self.places) == insert_batch_size:
            # insert new rows
            logging.info(f"Loading {len(self.places)} new places to table")
            self.session.bulk_save_objects(self.places)
            self.session.commit()
            self.places = list()


def main(db: OsmDB, osmfile: str, delete_first: bool = False):
    """Load data from osmfile to database"""
    s = Session(db.engine)

    # drop index before inserting
    s.execute("""DROP INDEX IF EXISTS geom_commercial_area_idx;""")
    s.commit()

    if delete_first:
        # delete any existing rows
        s.query(db.CommercialArea).delete()
        s.commit()

    # process osm file
    handler = PlaceHandler(table_obj=db.CommercialArea, session=s)
    handler.apply_file(osmfile)

    # load any remaining rows
    logging.info(f"Loading {len(handler.places)} new places to table")
    s.bulk_save_objects(handler.places)
    s.commit()

    if DEBUG:  # write out debug log for why a place was dropped from insert
        with open("debug_excluded.log", "w") as output:
            for x in handler.excluded:
                output.write(str(x) + "\n")

    # recreate index
    s.execute(
        """CREATE INDEX geom_commercial_area_idx ON commercial_area USING GIST (geom);"""
    )
    s.commit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract commercial area polygons and load to database"
    )
    parser.add_argument("osm_file", help="OSM file")
    parser.add_argument("--host", default="localhost", help="postgresql host")
    parser.add_argument("--port", default=5432, help="postgresql port")
    parser.add_argument("--user", default=getpass.getuser(), help="postgresql username")
    parser.add_argument("--password", default=None, help="postgresql password")
    parser.add_argument(
        "--database", default="osm_commercial", help="postgresql database"
    )
    parser.add_argument(
        "--debug", default=False, action="store_true", help="Run in debug mode"
    )
    parser.add_argument(
        "--echo", default=False, action="store_true", help="Echo database statements"
    )
    parser.add_argument(
        "--delete_first",
        default=False,
        action="store_true",
        help="Delete all rows in table before running",
    )

    args = parser.parse_args()
    DEBUG = args.debug
    USER = args.user

    logging.basicConfig(
        filename="places.log",
        level=logging.DEBUG if DEBUG else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    osm_db = OsmDB(
        host=args.host,
        port=args.port,
        username=args.user,
        password=args.password,
        database=args.database,
        echo=args.echo,
    )
    osm_db.test_connection()

    main(db=osm_db, osmfile=args.osm_file, delete_first=args.delete_first)
