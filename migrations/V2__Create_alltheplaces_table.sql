CREATE TABLE alltheplaces (
    id serial PRIMARY KEY,
    wikidata_id VARCHAR(20),
    "@spider" VARCHAR (50),
    ref VARCHAR (255),
    brand VARCHAR(255),
    name VARCHAR (255),
    website VARCHAR(255),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    modified_by VARCHAR (45) NOT NULL,
    modified_date TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_by VARCHAR (45),
    deleted_date TIMESTAMP
);

SELECT AddGeometryColumn('alltheplaces', 'geom', 4326, 'POINT', 2);
