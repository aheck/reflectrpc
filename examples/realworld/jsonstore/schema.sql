CREATE TABLE public.jsonstore
(
  uuid uuid NOT NULL,
  obj_name character varying,
  data jsonb,
  updated timestamp without time zone,
  CONSTRAINT pkey PRIMARY KEY (uuid),
  CONSTRAINT obj_name_uniq UNIQUE (obj_name)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.jsonstore
  OWNER TO postgres;
