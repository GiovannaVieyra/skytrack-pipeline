"""Mapeo de los state vectors de OpenSky

El endpoint /states/all devuelve cada avion como una lista donde la posicion determina el significado. 
Este archivo es la unica fuente de verdad de ese orden. 
Nunca acceder a un indice fuera de aca.

Referencia: https://openskynetwork.github.io/opensky-api/rest.html"""

import pyarrow as pa

ARROW_SCHEMA = pa.schema([
    ("snapshot_time", pa.int64()),
    ("icao24", pa.string()),
    ("callsign", pa.string()),
    ("origin_country", pa.string()),
    ("time_position", pa.int64()),
    ("last_contact", pa.int64()),
    ("longitude", pa.float64()),
    ("latitude", pa.float64()),
    ("baro_altitude", pa.float64()),
    ("on_ground", pa.bool_()),
    ("velocity", pa.float64()),
    ("true_track", pa.float64()),
    ("vertical_rate", pa.float64()),
    ("sensors", pa.list_(pa.int64())),
    ("geo_altitude", pa.float64()),
    ("squawk", pa.string()),
    ("spi", pa.bool_()),
    ("position_source", pa.int64()),
])

STATE_FIELDS = [
    "icao24",
    "callsign",
    "origin_country",
    "time_position",
    "last_contact",
    "longitude",
    "latitude",
    "baro_altitude",
    "on_ground",
    "velocity",
    "true_track",
    "vertical_rate",
    "sensors",
    "geo_altitude",
    "squawk",
    "spi",
    "position_source",
]

def parse_state(state):
    """Convierte una lista de OpenSky en un diccionario con nombres."""
    row = dict(zip(STATE_FIELDS, state))
    
    if row.get("callsign"):
        row["callsign"] = row["callsign"].strip() or None
    return row

def parse_state(state):
    """Pasa una lista de OpenSky en un diccionario con nombres."""
    row = dict(zip(STATE_FIELDS, state))
    
    if row.get("callsign"):
        row["callsign"] = row["callsign"].strip() or None
    return row

def parse_states(playload):
    """Pasa la respuesta completa de /states/all a una lista de dicts."""    
    timestamp = playload.get("time")
    states = playload.get("states") or []
    
    return [{"snapshot_time": timestamp, **parse_state(s)} for s in states]