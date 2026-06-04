from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from app.models.base import Base


class Busbar(Base):
    __tablename__ = "busbar"

    id = Column(Integer, primary_key=True)
    size = Column(String(100))
    material = Column(String(100))
    rating = Column(String(100))