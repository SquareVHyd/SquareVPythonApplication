from sqlalchemy import Column
from sqlalchemy import BigInteger
from sqlalchemy import Text
from sqlalchemy import Float

from app.models.base import Base


class PriceList(Base):

    __tablename__ = "tblPriceList"

    ID = Column(BigInteger, primary_key=True)

    ItemDescription = Column(Text)

    Model = Column(Text)

    ListPrice = Column(Float)

    DiscountPercent = Column(Float)

    NetPrice = Column(Float)

    UsedQty = Column(Float)

    TotalAmount = Column(Float)