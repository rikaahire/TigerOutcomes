#!/usr/bin/env python
import sqlalchemy
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# favorites table
class Favorites(Base):
    __tablename__ = 'favorites'

    name = Column(String, primary_key=True)
    soc_code = Column(String, primary_key=True)
    status = Column(Boolean, primary_key=True)
    
    def __repr__(self):
        return f"<Favorites(name={self.name}, soc_code={self.soc_code}, status={self.status})>"

# Database connection
DATABASE_URL = 'postgresql://tigeroutcomesdb_x9pf_user:Ewfihh7sXhDfzBS1JX51rem45ebypkqa@dpg-ctb2vm52ng1s73dphqqg-a.ohio-postgres.render.com/tigeroutcomesdb_x9pf'
engine = sqlalchemy.create_engine(DATABASE_URL)

# Create favorites table
def create_favorites_table():
    Base.metadata.create_all(engine)
    print("Favorites table created successfully.")

if __name__ == "__main__":
    create_favorites_table()
