from sqlalchemy import Column, BigInteger, Text
from app.models.base import Base


class Customer(Base):
    __tablename__ = 'tblCustomers'

    ID = Column('ID', BigInteger, primary_key=True)
    CustomerName = Column('CustomerName', Text)
    Mail = Column('Mail', Text)
    CustomerPhone = Column('CustomerPhone', Text)
    CustomerAddress = Column('CustomerAddress', Text)
    CustomerCity = Column('CustomerCity', Text)
    CustomerStateID = Column('CustomerStateID', BigInteger)
    CustomerPIN = Column('CustomerPIN', BigInteger)
    CustomerNotes = Column('CustomerNotes', Text)
    CustomerGSTNCode = Column('CustomerGSTNCode', Text)
    Attachments = Column('Attachments', Text)
    SysDateOfEntry = Column('SysDateOfEntry', Text)

    def __repr__(self):
        return f"<Customer(ID={self.ID}, CustomerName='{self.CustomerName}', Mail='{self.Mail}')>"