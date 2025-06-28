# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import heapq

from . import models, schemas, database # Assuming these are in the same package

# --- Database setup ---
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Hyderabad Metro Backend",
    description="Backend system for Hyderabad Metro Route Finder and Network Management",
    version="1.0.0",
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Graph Representation and Algorithms (within a service or helper) ---

class MetroGraph:
    def __init__(self, db: Session):
        self.graph: Dict[int, List[Tuple[int, dict]]] = defaultdict(list) # station_id -> [(neighbor_station_id, weight_dict)]
        self.station_map: Dict[str, List[models.Station]] = defaultdict(list) # station_name -> [list of Station objects (if same name on multiple lines)]
        self.station_id_to_obj: Dict[int, models.Station] = {} # station_id -> Station object
        self._build_graph(db)

    def _build_graph(self, db: Session):
        stations = db.query(models.Station).all()
        lines = db.query(models.Line).all()
        line_map = {line.id: line for line in lines}

        # Populate station maps
        for station in stations:
            self.station_map[station.name].append(station)
            self.station_id_to_obj[station.id] = station

        # Add edges for consecutive stations on the same line
        for line in lines:
            # Sort stations by station_number_on_line to ensure correct order
            sorted_stations = sorted([s for s in stations if s.line_id == line.id],
                                     key=lambda s: s.station_number_on_line)
            for i in range(len(sorted_stations) - 1):
                s1 = sorted_stations[i]
                s2 = sorted_stations[i+1]

                # Edge from s1 to s2
                self.graph[s1.id].append((s2.id, {
                    "stations": 1,
                    "time": 2.5,
                    "fare": 5.0 if s1.station_number_on_line >= 2 else 0.0, # Fare rules applied later for first 2 stations
                    "line_id": line.id
                }))
                # Edge from s2 to s1 (bidirectional)
                self.graph[s2.id].append((s1.id, {
                    "stations": 1,
                    "time": 2.5,
                    "fare": 5.0 if s2.station_number_on_line >= 2 else 0.0,
                    "line_id": line.id
                }))

        # Add transfer edges for interchange stations
        # Iterate through stations, group by name to find interchanges
        for station_name, stations_on_different_lines in self.station_map.items():
            if len(stations_on_different_lines) > 1 and all(s.is_interchange for s in stations_on_different_lines):
                # This is an interchange point, connect all versions of this station
                for i in range(len(stations_on_different_lines)):
                    for j in range(i + 1, len(stations_on_different_lines)):
                        s1 = stations_on_different_lines[i]
                        s2 = stations_on_different_lines[j]

                        # Ensure they are on different lines for an actual interchange
                        if s1.line_id != s2.line_id:
                            # Add an edge between the different line instances of the same interchange station
                            self.graph[s1.id].append((s2.id, {
                                "stations": 0, # No station count increase
                                "time": 5.0, # Interchange time
                                "fare": 2.0, # Interchange penalty
                                "line_change": True,
                                "from_line_id": s1.line_id,
                                "to_line_id": s2.line_id
                            }))
                            self.graph[s2.id].append((s1.id, {
                                "stations": 0,
                                "time": 5.0,
                                "fare": 2.0,
                                "line_change": True,
                                "from_line_id": s2.line_id,
                                "to_line_id": s1.line_id
                            }))

    def find_shortest_path(self, start_station_name: str, end_station_name: str) -> Optional[Dict]:
        start_nodes = self.station_map.get(start_station_name)
        end_nodes = self.station_map.get(end_station_name)

        if not start_nodes or not end_nodes:
            return None # Station not found

        # Dijkstra's implementation
        # Priority queue stores tuples: (current_cost, station_id, path_list, fare_total, time_total, current_line_id, num_stations_in_path)
        # We aim to minimize a combined cost, focusing on stations, then time, then fare
        # For simplicity in this example, let's optimize primarily by total stations.
        # A more complex heuristic for Dijkstra's (or A*) would be needed for a true "optimal" based on multiple criteria.
        # Here, we will just find path with min stations, then calculate fare/time for it.

        min_total_stations = float('inf')
        best_path_ids = []
        best_fare = 0.0
        best_time = 0.0
        best_interchanges = []
        best_line_changes = []

        # Iterate through all possible starting points (if start_station_name is an interchange)
        for start_node_obj in start_nodes:
            pq = [(0, start_node_obj.id, [start_node_obj.id], 0.0, 0.0, start_node_obj.line_id, 1)] # (stations_count, current_id, path_ids, current_fare, current_time, current_line, stations_visited_count_for_fare)
            distances = {s_id: float('inf') for s_id in self.station_id_to_obj.keys()}
            distances[start_node_obj.id] = 0

            # To store the full path, fare, time, line changes for each visited node
            path_info = {start_node_obj.id: {
                "path_ids": [start_node_obj.id],
                "fare": 0.0,
                "time": 0.0,
                "current_line_id": start_node_obj.line_id,
                "stations_in_segment": 1, # Number of stations in current segment for fare rule
                "interchanges": [],
                "line_changes": []
            }}

            visited = set()

            while pq:
                current_stations_count, current_station_id, current_path_ids, current_fare, current_time, current_line_id, stations_in_segment_for_fare = heapq.heappop(pq)

                if current_station_id in visited:
                    continue
                visited.add(current_station_id)

                current_station_obj = self.station_id_to_obj[current_station_id]

                # Check if we reached an end node
                if current_station_obj.name == end_station_name:
                    # Found a path, check if it's the shortest in terms of stations
                    if current_stations_count < min_total_stations:
                        min_total_stations = current_stations_count
                        best_path_ids = current_path_ids
                        best_fare = current_fare
                        best_time = current_time
                        best_interchanges = path_info[current_station_id]["interchanges"]
                        best_line_changes = path_info[current_station_id]["line_changes"]
                    continue # Continue to find other potential shorter paths for other start/end node combinations

                for neighbor_id, edge_weights in self.graph[current_station_id]:
                    neighbor_obj = self.station_id_to_obj[neighbor_id]
                    cost_to_neighbor = edge_weights["stations"] # Primary optimization metric

                    new_fare = current_fare
                    new_time = current_time
                    new_interchanges = list(path_info[current_station_id]["interchanges"])
                    new_line_changes = list(path_info[current_station_id]["line_changes"])
                    new_stations_in_segment_for_fare = stations_in_segment_for_fare

                    if "line_change" in edge_weights and edge_weights["line_change"]:
                        # This is an interchange edge
                        new_fare += edge_weights["fare"] # Interchange penalty
                        new_time += edge_weights["time"] # Interchange time
                        new_line_id = edge_weights["to_line_id"]
                        if current_station_obj.name not in new_interchanges:
                            new_interchanges.append(current_station_obj.name)
                        new_line_changes.append(schemas.LineChangeDetail(
                            _from=self.station_id_to_obj[current_station_id].line.name,
                            to=self.station_id_to_obj[neighbor_id].line.name,
                            at=current_station_obj.name
                        ))
                        # Reset segment station count after interchange for fare calculation on new line
                        new_stations_in_segment_for_fare = 0 # It will become 1 when we consider neighbor as first station
                    else:
                        # Regular station hop
                        new_time += edge_weights["time"]
                        new_line_id = edge_weights["line_id"] # Should be same as current_line_id

                        new_stations_in_segment_for_fare += 1
                        if new_stations_in_segment_for_fare <= 2:
                            new_fare += 0 # Base fare handled for first 2 stations
                        else:
                            new_fare += 5.0 # Additional fare after first 2 stations

                    # Update total stations count
                    new_total_stations_count = current_stations_count + cost_to_neighbor

                    if new_total_stations_count < distances.get(neighbor_id, float('inf')): # Simple Dijkstra for min stations
                        distances[neighbor_id] = new_total_stations_count
                        path_info[neighbor_id] = {
                            "path_ids": current_path_ids + [neighbor_id],
                            "fare": new_fare,
                            "time": new_time,
                            "current_line_id": new_line_id,
                            "stations_in_segment": new_stations_in_segment_for_fare,
                            "interchanges": new_interchanges,
                            "line_changes": new_line_changes
                        }
                        heapq.heappush(pq, (new_total_stations_count, neighbor_id, current_path_ids + [neighbor_id], new_fare, new_time, new_line_id, new_stations_in_segment_for_fare))

        if not best_path_ids:
            return None # No path found

        # Reconstruct path names
        route_names = [self.station_id_to_obj[s_id].name for s_id in best_path_ids]

        # Apply base fare logic for the first segment
        final_fare = best_fare
        # The fare rule "₹10 for the first 2 stations" implies a base cost.
        # This can be handled by adding ₹10 once if totalStations > 0.
        if min_total_stations > 0:
            final_fare += 10.0 # Base fare for starting a journey

        return {
            "route": route_names,
            "totalStations": min_total_stations,
            "totalFare": final_fare,
            "interchanges": list(set(best_interchanges)), # Ensure unique interchanges
            "estimatedTime": f"{best_time} minutes",
            "lineChanges": best_line_changes
        }


# Global graph instance (for simplicity, in a real app might be managed by a factory)
metro_graph: Optional[MetroGraph] = None

@app.on_event("startup")
async def startup_event():
    """Build the metro graph on application startup."""
    global metro_graph
    with next(get_db()) as db:
        metro_graph = MetroGraph(db)
    print("Metro graph built successfully on startup.")

# --- API Endpoints ---

# --- Line Management ---

@app.post("/api/lines", response_model=schemas.LineResponse, status_code=status.HTTP_201_CREATED)
async def create_line(line: schemas.LineCreate, db: Session = Depends(get_db)):
    db_line = db.query(models.Line).filter(models.Line.name == line.name).first()
    if db_line:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Line with name '{line.name}' already exists.")
    db_line = models.Line(**line.dict())
    db.add(db_line)
    db.commit()
    db.refresh(db_line)
    # Rebuild graph after changes
    global metro_graph
    metro_graph = MetroGraph(db)
    return db_line

@app.get("/api/lines", response_model=List[schemas.LineResponse])
async def list_lines(db: Session = Depends(get_db)):
    lines = db.query(models.Line).all()
    return lines

@app.get("/api/lines/{line_id}", response_model=schemas.LineResponse)
async def get_line_details(line_id: int, db: Session = Depends(get_db)):
    line = db.query(models.Line).filter(models.Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Line with ID {line_id} not found.")
    return line

@app.put("/api/lines/{line_id}", response_model=schemas.LineResponse)
async def update_line(line_id: int, line_update: schemas.LineUpdate, db: Session = Depends(get_db)):
    db_line = db.query(models.Line).filter(models.Line.id == line_id).first()
    if not db_line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Line with ID {line_id} not found.")

    existing_name_line = db.query(models.Line).filter(models.Line.name == line_update.name, models.Line.id != line_id).first()
    if existing_name_line:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Line with name '{line_update.name}' already exists.")

    for field, value in line_update.dict(exclude_unset=True).items():
        setattr(db_line, field, value)
    db.commit()
    db.refresh(db_line)
    # Rebuild graph after changes
    global metro_graph
    metro_graph = MetroGraph(db)
    return db_line

@app.delete("/api/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_line(line_id: int, db: Session = Depends(get_db)):
    line = db.query(models.Line).filter(models.Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Line with ID {line_id} not found.")

    # Check for associated stations
    stations_on_line = db.query(models.Station).filter(models.Station.line_id == line_id).count()
    if stations_on_line > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot delete line with ID {line_id} as it has associated stations. Delete stations first.")

    db.delete(line)
    db.commit()
    # Rebuild graph after changes
    global metro_graph
    metro_graph = MetroGraph(db)
    return

# --- Station Management ---

@app.post("/api/lines/{line_id}/stations", response_model=schemas.StationResponse, status_code=status.HTTP_201_CREATED)
async def add_station_to_line(line_id: int, station: schemas.StationCreate, db: Session = Depends(get_db)):
    line = db.query(models.Line).filter(models.Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Line with ID {line_id} not found.")

    # Check for unique station name on this line and unique station number on this line
    existing_station = db.query(models.Station).filter(
        models.Station.line_id == line_id,
        (models.Station.name == station.name) | (models.Station.station_number_on_line == station.station_number_on_line)
    ).first()
    if existing_station:
        if existing_station.name == station.name:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Station '{station.name}' already exists on line '{line.name}'.")
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Station number {station.station_number_on_line} is already taken on line '{line.name}'.")

    db_station = models.Station(**station.dict(), line_id=line_id)
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    db_station.line_name = line.name # Add line name for response convenience
    # Rebuild graph after changes
    global metro_graph
    metro_graph = MetroGraph(db)
    return db_station

@app.get("/api/lines/{line_id}/stations", response_model=List[schemas.StationResponse])
async def list_stations_on_line(line_id: int, db: Session = Depends(get_db)):
    line = db.query(models.Line).filter(models.Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Line with ID {line_id} not found.")

    stations = db.query(models.Station).filter(models.Station.line_id == line_id).order_by(models.Station.station_number_on_line).all()
    # Add line_name for each station in the response
    for s in stations:
        s.line_name = line.name
    return stations

@app.get("/api/stations", response_model=List[schemas.StationResponse])
async def list_all_stations(db: Session = Depends(get_db)):
    stations = db.query(models.Station, models.Line).join(models.Line).all()
    result = []
    for station, line in stations:
        station_response = schemas.StationResponse.from_orm(station)
        station_response.line_name = line.name
        result.append(station_response)
    return result

# --- Route Finding ---

@app.post("/api/route/find", response_model=schemas.RouteResponse)
async def find_metro_route(request: schemas.RouteRequest, db: Session = Depends(get_db)):
    if not metro_graph:
        # This shouldn't happen if startup event runs, but as a safeguard
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Metro graph not initialized. Please try again later.")

    # Re-initialize graph if data might have changed since last request (e.g. for development)
    # In a production setup, consider a caching layer and explicit graph refresh
    # or an event-driven update mechanism for the graph.
    # For this exercise, simple re-initialization on data changes via management APIs is assumed.
    # We already have `metro_graph = MetroGraph(db)` calls in line/station management APIs.
    # If the app runs long without management API calls, the graph could be stale.
    # For demonstration, we'll assume graph is up-to-date or re-built by management calls.

    if request.source == request.destination:
        return schemas.RouteResponse(
            route=[request.source],
            totalStations=0,
            totalFare=0.0,
            interchanges=[],
            estimatedTime="0 minutes",
            lineChanges=[]
        )

    # Validate station names exist in the system
    source_exists = db.query(models.Station).filter(models.Station.name == request.source).first()
    destination_exists = db.query(models.Station).filter(models.Station.name == request.destination).first()

    if not source_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid source station name: '{request.source}' not found.")
    if not destination_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid destination station name: '{request.destination}' not found.")

    path_result = metro_graph.find_shortest_path(request.source, request.destination)

    if not path_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No route found between '{request.source}' and '{request.destination}'.")

    return schemas.RouteResponse(**path_result)