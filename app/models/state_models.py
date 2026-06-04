from sqlalchemy import Column, BigInteger, Text
from app.models.base import Base


class State(Base):
    __tablename__ = 'tblState'

    ID = Column('ID', BigInteger, primary_key=True)
    StateCode = Column('StateCode', BigInteger, unique=True)
    StateName = Column('StateName', Text)

    def __repr__(self):
        return f"<State(ID={self.ID}, StateCode={self.StateCode}, StateName='{self.StateName}')>"
