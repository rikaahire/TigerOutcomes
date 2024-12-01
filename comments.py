#!/usr/bin/env python
import sqlalchemy
from sqlalchemy import Column, Integer, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Comments table
class Comments(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    replies = Column(JSON, default=[])

    def __repr__(self):
        return f"<Comments(id={self.id}, text={self.text}, replies={self.replies})>"

# Database connection
DATABASE_URL = 'postgresql://tigeroutcomesdb_user:CS1c7Vu0hFmPKvOLlSHymCpiHaAOKVjV@dpg-cspdgmrtq21c739rtrrg-a.ohio-postgres.render.com/tigeroutcomesdb'
engine = sqlalchemy.create_engine(DATABASE_URL)

# Create comments table
def create_comments_table():
    Base.metadata.create_all(engine)
    print("Comments table created successfully.")

if __name__ == "__main__":
    create_comments_table()
