CREATE TABLE IF NOT EXISTS dbo.url_domain
(
    id SERIAL PRIMARY KEY,
    subdomain_name text COLLATE pg_catalog."default",
    domain_name text COLLATE pg_catalog."default" UNIQUE,
    suffix text COLLATE pg_catalog."default",
    paywall_method character varying(100) COLLATE pg_catalog."default" NOT NULL DEFAULT 'no_method'::character varying,
    checked boolean NOT NULL DEFAULT false
);

CREATE TABLE dbo.web_archive_new(
	id SERIAL,
	new_id integer NOT NULL DEFAULT '-1'::integer,
	potential_urls text[] COLLATE pg_catalog."default",
	is_empty boolean NOT NULL DEFAULT false,
	is_retrieved boolean NOT NULL DEFAULT false,
	data_source text COLLATE pg_catalog."default"
);

CREATE TABLE dbo.raw_new(
	id SERIAL,
	new_id integer NOT NULL DEFAULT '-1'::integer,
	original_url text COLLATE pg_catalog."default" NOT NULL,
	raw_new BYTEA NOT NULL DEFAULT '',
	reader_mode_new BYTEA NOT NULL DEFAULT '',
	is_empty boolean NOT NULL DEFAULT false,
	is_retrieved boolean NOT NULL DEFAULT false,
	parsed boolean NOT NULL DEFAULT false,
	should_rescrape boolean NOT NULL DEFAULT false,
	data_source text COLLATE pg_catalog."default"
);

CREATE TABLE dbo.preloaded_content
(
    id SERIAL,
    data_source character varying(200) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT data_source_pkey PRIMARY KEY (data_source)
);