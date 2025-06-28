# schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional

# --- Line Schemas ---
class LineBase(BaseModel):
    name: str
    color: str

class LineCreate(LineBase):
    pass

class LineUpdate(LineBase):
    pass

class LineResponse(LineBase):
    id: int

    class Config:
        from_attributes = True

# --- Station Schemas ---
class StationBase(BaseModel):
    name: str = Field(..., example="Miyapur")
    distance_from_previous_station: Optional[float] = Field(None, description="Distance in KM from the previous station on the same line. 0.0 for the first station.")
    station_number_on_line: int = Field(..., description="The sequential number of the station on its line, starting from 1.")
    is_interchange: bool = Field(False, description="True if this station is an interchange station.")

class StationCreate(StationBase):
    pass

class StationResponse(StationBase):
    id: int
    line_id: int
    line_name: Optional[str] = None # Added for convenience in /api/stations

    class Config:
        from_attributes = True

# --- Route Finding Schemas ---
class RouteRequest(BaseModel):
    source: str = Field(..., example="Miyapur")
    destination: str = Field(..., example="Hitec City")

class LineChangeDetail(BaseModel):
    from_line: str = Field(..., alias="from", description="Original line name")
    to: str = Field(..., description="New line name")
    at: str = Field(..., description="Interchange station name")

class RouteResponse(BaseModel):
    route: List[str] = Field(..., description="List of station names in the optimal route")
    totalStations: int
    totalFare: float
    interchanges: List[str] = Field(..., description="List of interchange station names encountered")
    estimatedTime: str = Field(..., description="Estimated travel time in human-readable format")
    lineChanges: List[LineChangeDetail] = Field(..., description="Details of line changes")