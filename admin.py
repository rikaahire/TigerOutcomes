#!/usr/bin/env python
import sqlalchemy
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# favorites table
class Favorites(Base):
    __tablename__ = 'admin'

    name = Column(String, primary_key=True)
    
    def __repr__(self):
        return f"<Admin(name={self.name})>"

# Database connection
DATABASE_URL = 'postgresql://tigeroutcomesdb_user:CS1c7Vu0hFmPKvOLlSHymCpiHaAOKVjV@dpg-cspdgmrtq21c739rtrrg-a.ohio-postgres.render.com/tigeroutcomesdb'
engine = sqlalchemy.create_engine(DATABASE_URL)

# Create favorites table
def create_favorites_table():
    Base.metadata.create_all(engine)
    print("Favorites table created successfully.")

if __name__ == "__main__":
    create_favorites_table()
