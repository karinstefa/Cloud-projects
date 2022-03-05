#%%
import pandas as pd
import re
import io
from unicodedata import normalize
from sqlalchemy import create_engine

def create_tables():
    """ create tables in the PostgreSQL database"""
    #%%
    host = 'database-2.cnjddgnl0ynw.us-east-1.rds.amazonaws.com'
    port = 5432
    user = 'postgres'
    password = 'cloud1234'
    database = 'db_concursos'

    #%%
    conneDB = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    conn = conneDB.raw_connection()
    cur = conn.cursor()
    #%%


    commands = (
        """
        CREATE TABLE "administradores" (
        "id" SERIAL PRIMARY KEY,
        "nombres" varchar,
        "apellidos" varchar,
        "correo" varchar,
        "password" varchar
        )""",
        """
        CREATE TABLE "concursos" (
        "id" SERIAL PRIMARY KEY,
        "id_admin" int,
        "nombre" varchar,
        "path_banner" varchar,
        "fecha_inicio" date,
        "fecha_fin" date,
        "valor_premio" varchar,
        "guion" varchar,
        "recomendaciones" varchar,
        "url" varchar
        )
        """,
        """
        CREATE TABLE "voces" (
        "id" SERIAL PRIMARY KEY,
        "id_concurso" int,
        "nombres" varchar,
        "apellidos" varchar,
        "correo" varchar,
        "path_original" varchar,
        "path_convertido" varchar,
        "observaciones" varchar,
        "fecha_creacion" date,
        "estado" int
        )""")
    

    try:
        for command in commands:
            cur.execute(command)
            # close communication with the PostgreSQL database server
        cur.close()
            # commit the changes
        conn.commit()

    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    create_tables()


# %%
