"""Печатает SQL-схему для Supabase (Postgres) из моделей: python -m app.schema > ../supabase/migrations/0001_init.sql"""
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from . import models  # noqa: F401
from .db import Base

print("-- Сгенерировано из server/app/models.py командой python -m app.schema\n")
for t in Base.metadata.sorted_tables:
    print(str(CreateTable(t).compile(dialect=postgresql.dialect())).strip() + ";\n")
    for i in t.indexes:
        print(str(CreateIndex(i).compile(dialect=postgresql.dialect())).strip() + ";")
    print(f"ALTER TABLE {t.name} ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу\n")
