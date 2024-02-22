CREATE TABLE IF NOT EXISTS dbo.parsed_new
(
    id SERIAL PRIMARY KEY,
    new_id integer NOT NULL DEFAULT '-1'::integer,
	title TEXT COLLATE pg_catalog."default",
	body TEXT COLLATE pg_catalog."default",
	publish_date timestamp,
	authors TEXT[] COLLATE pg_catalog."default",
    language TEXT COLLATE pg_catalog."default",
    top_image_url TEXT COLLATE pg_catalog."default" ,
    media_content_urls TEXT[] COLLATE pg_catalog."default",
    is_empty bool DEFAULT FALSE,
    data_source text COLLATE pg_catalog."default"
);
