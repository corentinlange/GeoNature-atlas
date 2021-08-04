-------- CRÉATION DU SCHÉMA -------------
CREATE SCHEMA utilisateurs AUTHORIZATION geonatadmin;

-------- CRÉATION DES TABLES ------------

-- TABLE bib_organisme
CREATE FOREIGN TABLE utilisateurs.bib_organismes (
    id_organisme int4 OPTIONS(column_name 'id_organisme') NOT NULL,
    uuid_organisme uuid OPTIONS(column_name 'uuid_organisme') NULL,
    nom_organisme varchar(500) OPTIONS(column_name 'nom_organisme') NULL,
    adresse_organisme varchar(128) OPTIONS(column_name 'adresse_organisme') NULL,
    cp_organisme varchar(5) OPTIONS(column_name 'cp_organisme') NULL,
    ville_organisme varchar(50) OPTIONS(column_name 'ville_organisme') NULL,
    tel_organisme varchar(14) OPTIONS(column_name 'tel_organisme') NULL,
    fax_organisme varchar(14) OPTIONS(column_name 'fax_organisme') NULL,
    email_organisme varchar(100) OPTIONS(column_name 'email_organisme') NULL,
    url_organisme varchar(255) OPTIONS(column_name 'url_organisme') NULL,
    url_logo varchar(255) OPTIONS(column_name 'url_logo') NULL,
    id_parent int4 OPTIONS(column_name 'id_parent') NULL,
)
SERVER geonaturedbserver
OPTIONS (schema_name 'utilisateurs', table_name 'bib_organismes');

-- TABLE cor_data_actor
CREATE FOREIGN TABLE utilisateurs.cor_data_actor (
    id_cda int4 OPTIONS(column_name 'id_cda') NOT NULL,
    id_dataset int4 OPTIONS(column_name 'id_dataset') NULL,
    id_role int4 OPTIONS(column_name 'id_role') NULL,
    id_organism int4 OPTIONS(column_name 'id_organism') NULL,
    id_nomenclature_actor_role int4 OPTIONS(column_name 'id_nomenclature_actor_role') NULL,
)
SERVER geonaturedbserver
OPTIONS (schema_name 'gn_meta', table_name 'cor_dataset_actor');

--CRÉATION VUE MATÉRIALISÉE
CREATE MATERIALIZED VIEW atlas.vm_organismes
TABLESPACE pg_default
AS SELECT count(*) as nb_observations, id_organisme , nom_organisme , adresse_organisme , cp_organisme , ville_organisme , tel_organisme , email_organisme , url_organisme ,url_logo , cd_ref
   FROM utilisateurs.bib_organismes bo
     JOIN utilisateurs.cor_dataset_actor cda ON bo.id_organisme =cda.id_organism JOIN synthese.synthese s ON s.id_dataset =cda.id_dataset join taxonomie.taxref t on s.cd_nom=t.cd_nom
  group by t.cd_ref, bo.id_organismes
WITH DATA;

