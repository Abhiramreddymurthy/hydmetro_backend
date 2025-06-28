# models.py (Simplified SQLAlchemy ORM definitions)

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Line(Base):
    __tablename__ = "lines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    color = Column(String, nullable=False)

    stations = relationship("Station", back_populates="line", order_by="Station.station_number_on_line")

    def __repr__(self):
        return f"<Line(id={self.id}, name='{self.name}', color='{self.color}')>"

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False) # Station name, potentially not unique globally if same name exists on different lines, but check for line+name uniqueness.
    line_id = Column(Integer, ForeignKey("lines.id"), nullable=False)
    distance_from_previous_station = Column(DECIMAL(5, 2), nullable=True) # Distance from previous station on THIS line
    station_number_on_line = Column(Integer, nullable=False) # Order of the station on the line
    is_interchange = Column(Boolean, default=False, nullable=False)

    line = relationship("Line", back_populates="stations")

    def __repr__(self):
        return f"<Station(id={self.id}, name='{self.name}', line_id={self.line_id}, station_number={self.station_number_on_line})>"

# Note: For interchange stations like Ameerpet, there will be *two* Station entries
# in the database, one for Red Line and one for Blue Line, both with 'is_interchange=True'
# and the same 'name'. The graph construction will link these logical nodes.