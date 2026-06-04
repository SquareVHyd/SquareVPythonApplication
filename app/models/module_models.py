from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey

from app.models.base import Base


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    module_name = Column(String(200))
    panel_id = Column(Integer, ForeignKey("panels.id"))