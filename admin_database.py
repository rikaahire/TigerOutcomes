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

# admin scope capabilities
#-----------------------------------------------------------------------

# get list of admins
def get_admins():
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('admin', metadata, autoload_with=engine)

    with engine.connect() as conn:
        rows = conn.execute(select(table)).fetchall()
    return [{"Admin": row.name} for row in rows]

# add a new admin
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

# remove an admin
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

# check if name is on admin list
def check_admin(username):
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('admin', metadata, autoload_with=engine)
    ret = False
    with engine.connect() as conn:
        rows = conn.execute(select(table).where(table.c.name == username)).fetchall()
        if len(rows) > 0:
            ret = True
    return ret

# admin comment capabilities
#-----------------------------------------------------------------------

# get all user-flagged comments
def fetch_flagged_comments():
    metadata = sqlalchemy.MetaData()
    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    stmt = select(table).where(table.c.valid == False)
    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()
    return [{"id": row.id, "text": row.text} for row in rows]

# approve a comment (don't remove)
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

# remove a comment (when not approved)
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

# clear comments database
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

# get all column names
def get_cols():
    metadata = sqlalchemy.MetaData()
    cols = {}

    table = sqlalchemy.Table('comments', metadata, autoload_with=engine)
    cols['comments'] = [column.name for column in table.columns]

    table = sqlalchemy.Table('admin', metadata, autoload_with=engine)
    cols['admin'] = [column.name for column in table.columns]

    return cols

#-----------------------------------------------------------------------

def main():

    cols = get_cols()
    for key, value in cols.items():
        print(key + ":")
        print(value)
        print("\n")

if __name__ == '__main__':
    main()
