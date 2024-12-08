#!/usr/bin/env python
import sqlalchemy
from sqlalchemy import Column, Integer, Text, JSON, Boolean, String, select
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Comments table
class Comments(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String)
    soc_code = Column(String)
    text = Column(Text, nullable=False)
    valid = Column(Boolean, default=False)
    replies = Column(JSON, default=[])

    def __repr__(self):
        return f"<Comments(id={self.id}, user = {self.user}, soc_code = {self.soc_code}, text={self.text}, valid={self.valid}, replies={self.replies})>"

# Database connection
DATABASE_URL = 'postgresql://tigeroutcomesdb_bwj0_user:SRIUMH9M3bEZ4uC2y879IVc7DHPvX9Uj@dpg-ctb1npt2ng1s73dpcnqg-a.ohio-postgres.render.com/tigeroutcomesdb_bwj0'
engine = sqlalchemy.create_engine(DATABASE_URL)

# Create comments table
def create_comments_table():
    Base.metadata.create_all(engine)
    print("Comments table created successfully.")

if __name__ == "__main__":
    create_comments_table()
