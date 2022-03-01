CREATE TABLE "administradores" (
  "id" SERIAL PRIMARY KEY,
  "nombres" varchar,
  "apellidos" varchar,
  "correo" varchar,
  "password" varchar
);

CREATE TABLE "concursos" (
  "id" SERIAL PRIMARY KEY,
  "id_admin" int,
  "nombre" varchar,
  "path_banner" varchar,
  "fecha_inicio" datetime,
  "fecha_fin" datetime,
  "valor_premio" varchar,
  "guion" varchar,
  "recomendaciones" varchar,
  "url" varchar
);

CREATE TABLE "voces" (
  "id" SERIAL PRIMARY KEY,
  "id_concurso" int,
  "nombres" varchar,
  "apellidos" varchar,
  "correo" varchar,
  "path_original" varchar,
  "path_convertido" varchar,
  "observaciones" varchar,
  "fecha_creacion" datetime,
  "estado" int
);

