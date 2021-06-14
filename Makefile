SHELL := /bin/bash
ATP_DOWNLOAD_URL = $(shell curl -s https://data.alltheplaces.xyz/runs/latest/info_embed.html | grep href | cut -d '"' -f2)
#OSM_EXTRACT_URL = http://download.geofabrik.de/north-america/us/texas-latest.osm.pbf
OSM_EXTRACT_URL = http://download.geofabrik.de/north-america/us-latest.osm.pbf
OSM_EXTRACT_NAME = $(shell basename $(OSM_EXTRACT_URL))

.PHONY : download_atp download_osm osm_extract dropdb initdb migratedb

download_atp :
	curl $(ATP_DOWNLOAD_URL) --output alltheplaces.tar.gz
	mkdir -p data/alltheplaces
	tar -xf alltheplaces.tar.gz --directory data/alltheplaces
	rm alltheplaces.tar.gz

download_osm :
	curl $(OSM_EXTRACT_URL) --output $(OSM_EXTRACT_NAME)

osm_extract :
	rm -f latest-extract.osm.pbf
	osmium tags-filter -v --progress --overwrite -o extract-$(OSM_EXTRACT_NAME) --expressions=filter_expressions.txt $(OSM_EXTRACT_NAME)

osm : download_osm osm_extract
	rm -f $(OSM_EXTRACT_NAME)

# database commands
migratedb :
	flyway -configFile=flyway.conf -user=$(USER) -password=$(PGPASS) migrate

initdb :
	# initdb osm_commercial # mac only
	createdb osm_commercial
	psql -d osm_commercial -c "CREATE EXTENSION postgis;"

dropdb :
	dropdb --if-exists osm_commercial

cleandb : dropdb initdb migratedb

fmt :
	black osm_commercial
	black *.py
	black tests

test :
	pytest -vv

python_install :
	python3 -m venv venv
	source venv/bin/activate
	pip install -r requirements.frozen

import_osm :
	python import_areas.py --password $(PGPASS) --debug extract-$(OSM_EXTRACT_NAME)

import_atp :
	python import_alltheplaces.py --password $(PGPASS) --debug data/alltheplaces/output
