#!/usr/bin/env python
import sqlalchemy
from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Admin table
class Admin(Base):
    __tablename__ = 'admin'

    name = Column(String, primary_key=True)
    
    def __repr__(self):
        return f"<Admin(name={self.name})>"

# Database connection
DATABASE_URL = 'postgresql://tigeroutcomesdb_x9pf_user:Ewfihh7sXhDfzBS1JX51rem45ebypkqa@dpg-ctb2vm52ng1s73dphqqg-a.ohio-postgres.render.com/tigeroutcomesdb_x9pf'
engine = sqlalchemy.create_engine(DATABASE_URL)

# Create favorites table
def create_admin_table():
    Base.metadata.create_all(engine)
    print("Admin table created successfully.")

if __name__ == "__main__":
    create_admin_table()
