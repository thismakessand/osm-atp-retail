CREATE TABLE commercial_area (
    id serial PRIMARY KEY,
    name VARCHAR (255),
    source VARCHAR (255),
    source_id VARCHAR (100),
    place_type VARCHAR (255),
    city VARCHAR (100),
    admin1 VARCHAR (100),
    postal_code VARCHAR (100),
    country VARCHAR (2),
    modified_by VARCHAR (45) NOT NULL,
    modified_date TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_by VARCHAR (45),
    deleted_date TIMESTAMP
);

SELECT AddGeometryColumn('commercial_area', 'geom', 4326, 'MULTIPOLYGON', 2);
