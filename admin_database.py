#!/usr/bin/env python
import keyring
import os
import sys
import argparse
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy import select, distinct, delete
from sqlalchemy.exc import SQLAlchemyError
import dotenv

#-----------------------------------------------------------------------

dotenv.load_dotenv()
DATABASE_URL = 'postgresql://tigeroutcomesdb_x9pf_user:Ewfihh7sXhDfzBS1JX51rem45ebypkqa@dpg-ctb2vm52ng1s73dphqqg-a.ohio-postgres.render.com/tigeroutcomesdb_x9pf'
#DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
engine = sqlalchemy.create_engine(DATABASE_URL)

default_limit = 10
#-----------------------------------------------------------------------

def fetch_flagged_comments():
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    stmt = select(table).where(table.c.valid == False)
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()
    return [{"id": row.id, "text": row.text} for row in rows]

def add_admin(username):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('admin', metadata, autoload_with=engine)
    ret = ''
    with engine.connect() as conn:
        try:
            stmt = table.insert().values(name=username)
            conn.execute(stmt)
            ret = f"Added new admin: {username}."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error adding admin: {e}"
            conn.rollback()
    return ret

def remove_admin(username):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('admin', metadata, autoload_with=engine)
    ret = ''
    with engine.connect() as conn:
        try:
            stmt = delete(table).where(table.c.name == username)
            conn.execute(stmt)
            ret = f"Added new admin: {username}."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error adding admin: {e}"
            conn.rollback()
    return ret

def check_admin(username):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('admin', metadata, autoload_with=engine)
    ret = False
    with engine.connect() as conn:
        rows = conn.execute(select(table).where(table.c.name == username)).fetchall()
        if len(rows) > 0:
            ret = True
    return ret

def approve(id):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    stmt = select(table).where(table.c.id == id)
    ret = ''
    with engine.connect() as conn:
        try:
            favorite = conn.execute(stmt).fetchall()
            if favorite:
                new_stmt = table.update().where(table.c.id == id).values(valid=True)
                conn.execute(new_stmt)
                ret = f"Approved comment with id: {id}."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error approving comment: {e}"
            conn.rollback()
    return ret

def remove(id):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    ret = ''
    with engine.connect() as conn:
        try:
            stmt = delete(table).where(table.c.id == id)
            conn.execute(stmt)
            ret = f"Removed comment with id: {id}."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error approving comment: {e}"
            conn.rollback()
    return ret

def removeAll():
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    ret = ''
    with engine.connect() as conn:
        try:
            stmt = delete(table)
            conn.execute(stmt)
            ret = f"Removed all comments."
            conn.commit()
        except SQLAlchemyError as e:
            ret = f"Error approving comment: {e}"
            conn.rollback()
    return ret

def get_admins():
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('admin', metadata, autoload_with=engine)
    with engine.connect() as conn:
        rows = conn.execute(select(table)).fetchall()
    return [{"Admin": row.name} for row in rows]

# get all column names (for use with get_rows for column names)
def get_cols():
    metadata = sqlalchemy.MetaData()
    cols = {}

    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    cols['comments'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('admin', metadata, autoload_with=engine)
    cols['admin'] = [column.name for column in table.columns]

    return cols

#-----------------------------------------------------------------------

# generic when given table, column, and equal
def get_rows(table_name, col_name, query, limit=default_limit):
    # input: table_name (sqlalchemy.Table): query table , col_name (str): target str, 
    #   query (str): rows we want to match
    #   limit (int): maximum number of rows that we want to return
    # output: finds all rows in table where row.col_name = query

    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table = sqlalchemy.Table(table_name, metadata, autoload_with=engine)

    # Create a select query
    stmt = select(table).where(table.c[col_name] == query).limit(limit)

    # Execute the query and fetch the results
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return rows

#-----------------------------------------------------------------------

# generic for all options (should be initial)
def get_all_instances(table_name, col_name):
    # input: table name and column name
    # output: returns a list of all unique rows within the column

    metadata = sqlalchemy.MetaData()
    metadata.reflect(engine)

    # Get table
    table = sqlalchemy.Table(table_name, metadata, autoload_with=engine)

    # Create a select query
    stmt = select(distinct(table.c[col_name]))

    # Execute the query and fetch the results
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return rows

def main():

    cols = get_cols()
    for key, value in cols.items():
        print(key + ":")
        print(value)
        print("\n")
    # rows = get_rows("demographics", 10)
    # for row in rows:
    #     print(row)

if __name__ == '__main__':
    main()
