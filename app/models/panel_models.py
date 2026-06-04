from sqlalchemy import Column, BigInteger, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Panel(Base):
    __tablename__ = "tbl_Panels"

    ID = Column(BigInteger, primary_key=True)
    QuoteID = Column(BigInteger, ForeignKey("tbl_QuoteMain.ID"))
    PanelCategory = Column(Text)
    PanelSerial = Column(Text)
    PanelName = Column(Text)
    PanelQty = Column(Integer)
    LengthXmm = Column(Integer)
    HeightYmm = Column(Integer)
    DepthZmm = Column(Integer)
    AddWaste = Column(Integer)
    PanelKARating = Column(Text)
    EarthRuns = Column(Text)
    StandRequired = Column(Text)
    BusbarMaterial = Column(Text)

    # Relationships
    modules = relationship("PanelModule", back_populates="panel", cascade="all, delete-orphan")
    steel = relationship("PanelSteel", back_populates="panel", uselist=False, cascade="all, delete-orphan")
    busbar = relationship("PanelBB", back_populates="panel", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Panel(ID={self.ID}, PanelName='{self.PanelName}', QuoteID={self.QuoteID})>"


class PanelModule(Base):
    __tablename__ = "tbl_PanelModules"

    ID = Column(BigInteger, primary_key=True)
    PanelID = Column(BigInteger, ForeignKey("tbl_Panels.ID"))
    IngOg = Column(Text)
    PanelModQty = Column(Integer)
    ModuleTypeID = Column(BigInteger, ForeignKey("tbl_PnlModuleCost.ID"))
    ModPole = Column(Text)
    ModKa = Column(Text)
    Release = Column(Text)
    Protection = Column(Text)
    Remark = Column(Text)

    # Relationships
    panel = relationship("Panel", back_populates="modules")

    def __repr__(self):
        return f"<PanelModule(ID={self.ID}, PanelID={self.PanelID})>"


class PanelSteel(Base):
    __tablename__ = "tbl_PanelSteel"

    ID = Column(BigInteger, primary_key=True)
    PanelID = Column(BigInteger, ForeignKey("tbl_Panels.ID"))
    FrontBackQty = Column(Integer)
    FrontBackSteelSize = Column(Text)
    SidesQty = Column(Integer)
    SidesSteelSize = Column(Text)
    BottomTopQty = Column(Integer)
    BottomSteelSize = Column(Text)
    TypeOfSeating = Column(Text)
    Canopy = Column(Text)
    IndoorOutdoor = Column(Text)
    PanelFace = Column(Text)
    DoubleDoor = Column(Text)
    DrawoutFixed = Column(Text)
    ProtectionClass = Column(Text)
    CableEntry = Column(Text)
    Mounting = Column(Text)
    SeatStand = Column(Text)
    StandMetalSize = Column(Text)

    # Relationships
    panel = relationship("Panel", back_populates="steel")

    def __repr__(self):
        return f"<PanelSteel(ID={self.ID}, PanelID={self.PanelID})>"


class PanelBB(Base):
    __tablename__ = "tbl_PanelBB"

    ID = Column(BigInteger, primary_key=True)
    PanelID = Column(BigInteger, ForeignKey("tbl_Panels.ID"))
    NeutralRating = Column(Integer)
    BusSection = Column(Text)
    BusSectionQty = Column(Integer)
    AmpsRequested = Column(Integer)
    AmpsSelected = Column(Text)
    BusbarClearence = Column(Text)
    BB_QtyPH = Column(Integer)
    BB_QtyNu = Column(Integer)
    BB_QtyEarth = Column(Integer)
    Select_BB_Phase = Column(Text)
    Select_BB_Neutral = Column(Text)
    Select_BB_Earth = Column(Text)

    # Relationships
    panel = relationship("Panel", back_populates="busbar")

    def __repr__(self):
        return f"<PanelBB(ID={self.ID}, PanelID={self.PanelID})>"


class PanelAccessory(Base):
    __tablename__ = "tbl_panelAccessories"

    ID = Column(BigInteger, primary_key=True)
    Description = Column(Text)
    Qty = Column(Integer)
    Unit = Column(Text)
    Price = Column(Integer)

    def __repr__(self):
        return f"<PanelAccessory(ID={self.ID}, Description='{self.Description}')>"