osm-commercial
==============
Explore commercial + retail areas from OpenStreetMap with commercial + retail points from 
[alltheplaces](https://www.github.com/alltheplaces/alltheplaces)


## Background

There are currently ~120,000 commercial/retail areas in the US in OSM without a name value and another ~1,500 
malls without names.

[alltheplaces](https://www.github.com/alltheplaces/alltheplaces) is an open data project that contains POI data scraped from company websites 
(think "Find a Store Near Me"-type locator pages).  There's currently >400 unique (non-broken) sources,
containing ~750,000 locations.  Many branch locations have location-specific name data that helps disambiguate that 
branch from other branches of the same chain, eg "Foot Locker Northpark Mall" vs "Foot Locker". Since many chains 
do this, we could use these individual locations to find overlapping strings in the names and potentially determine
(or suggest!) a good name for a nameless OSM commercial/retail/mall area via consensus.

For example, this nameless OSM mall area intersects with these names from alltheplaces data:  
[way/401654342](https://www.openstreetmap.org/way/401654342)
```
{
    Huntington,
    Zales Jewelers Huntington Mall,
    Piercing Pagoda Huntington Mall,
    Visionworks Huntington Mall,
    Shop Ear Piercings & Jewelry at HUNTINGTON MALL,
    Foot LockerHuntington Mall,
    Huntington Mall,
    Huntington Mall,
    Hungtington Mall,
    HUNTINGTON MALL,
    BARBOURSVILLE MALL,
    Kay Jewelers Huntington Mall,
    Huntington Mall,
    Huntington Mall,
    Barboursville,
    Huntington Mall 2,
    Huntington Mall
}
```

## Usage

To set up the database:
```
make initdb
make migratedb
```

To drop the database and rebuild from scratch:
```
make cleandb
```

To download the OSM extract and coarse-filter via osmium:
```
make download_osm
make extract_osm
```

To download and untar the alltheplaces data:
```
make download_atp
```

To setup python env:
```
make python_install
```

To run the tests:
```
make test
```

There are two scripts:
 - `import_areas.py` for loading commercial + retail polygons from OSM
      
    This script loads from a osm .pbf extract and uses the Python osmium bindings (pyosmium) to extract and filter
    features for loading into a postgresql table.  
    There is a lot of bad and/or mis-tagged data in OSM so I set up some rules based on tags and values found in the `name` key.
    These rules can be found here: `osm_commercial/exclude.py`
    
    ```
    make import_osm
    ```
      
 - `import_alltheplaces.py` for loading point data from alltheplaces sources
 
    This script iterates over a directory of geojson files from the alltheplaces project and loads all non-empty
    files.

    ```
    make import_atp
    ```

After the data is loaded, we can query the data in postgres  

eg, get all the names that intersect with a mall with no name:  
```
SELECT 
	commercial_area.source_id,
	ARRAY_AGG(alltheplaces.name) as names
FROM commercial_area
JOIN alltheplaces
ON ST_Contains(commercial_area.geom, alltheplaces.geom)
WHERE commercial_area.name IS NULL
	AND alltheplaces.name IS NOT null
	and commercial_area.place_type in ('mall')
GROUP BY commercial_area.source_id
```

#### Requirements:

- osmium   
MacOS: `brew install osmium-tool`  
Linux: `sudo apt-get install osmium-tool`

- flyway
    https://flywaydb.org/documentation/usage/commandline/
    
