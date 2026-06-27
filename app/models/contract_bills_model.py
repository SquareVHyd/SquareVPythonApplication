from sqlalchemy import Column, Date, String, Numeric, BigInteger, ForeignKey
from app.models.base import Base

class ContractBill(Base):
    __tablename__ = 'Contract_Bills'
    __table_args__ = {'schema': 'public'}

    Bill_No = Column(BigInteger, primary_key=True, autoincrement=True)
    Bill_Date = Column(Date, nullable=False)
    Contractor_Name = Column(String, nullable=False)
    Type_Of_Job = Column(String, nullable=False)
    Amount = Column(Numeric(12, 2), nullable=False)
    Project_Name = Column(String, nullable=False)
    PO_ID = Column(BigInteger, ForeignKey('public.po_Customer.ID', ondelete='CASCADE', onupdate='CASCADE'))
    PO_No = Column(BigInteger)
