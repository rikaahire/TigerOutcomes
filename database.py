#!/usr/bin/env python

import pandas as pd
import psycopg2
from psycopg2 import sql
import argparse
import sys

DATABASE_URL = 'postgresql://bz5989@localhost:5432/mydb'

# Mount path to SMB share
smb_mount_path = "/Volumes/TigerOutcomes/"

# xlsx files and corresponding PostgreSQL tables
files_to_tables = {
    "COS333_AcA_Student_Outcomes.xlsx": "student_outcomes",
    "COS333_Demographics.xlsx": "demographics",
    "COS333_NSC_ST_Degrees2.xlsx": "st_degrees"
}

def load_data_to_postgres(file_path, table_name):
    # Read xlsx file into pandas df
    df = pd.read_excel(file_path)

    # Connect to PostgreSQL
    with psycopg2.connect(DATABASE_URL) as connection:
        cursor = connection.cursor()

        for _, row in df.iterrows():
            columns = list(df.columns)
            values = [row[col] for col in columns]
            insert_statement = sql.SQL(
                "INSERT INTO {} ({}) VALUES ({})"
            ).format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(values))
            )
            cursor.execute(insert_statement, values)

        print("Data loaded")

# Load files

def main():
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description='Database running')
    parser.add_argument('load', nargs='?',
        help='load in data?')
    load = parser.parse_args().load

    try:
        if load is not None:
            for file_name, table_name in files_to_tables.items():
                load_data_to_postgres(smb_mount_path + file_name, table_name)
        else:
            print("Didn't choose to load data")
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()