from sqlalchemy import Column, Integer, String, Text
from db import Base

class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    url = Column(String)
