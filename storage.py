from datetime import datetime, timezone
from pathlib import Path
from schema import ARROW_SCHEMA
import pyarrow as pa
import pyarrow.parquet as pq

DATA_DIR = Path("data/raw")

def particion_path(snapshot_time):
    """Devuelve la carpeta donde va un snapshot, segun su timestamp UTC."""

    dt = datetime.fromtimestamp(snapshot_time, tz=timezone.utc)
    return DATA_DIR / f"year={dt.year:04d}" / f"month={dt.month:02d}" / f"day={dt.day:02d}" / f"hour={dt.hour:02d}"

def escribir_snapshot(rows):
    """Escribe una lista de dicts como un archivo Parquet. Devuelve la ruta."""
    if not rows:
        return None
    
    snapshot_time = rows[0]["snapshot_time"]
    carpeta = particion_path(snapshot_time)
    carpeta.mkdir(parents=True, exist_ok=True)
    
    destino = carpeta / f"snapshot_{snapshot_time}.parquet"
    
    tabla = pa.Table.from_pylist(rows, schema=ARROW_SCHEMA)
    pq.write_table(tabla, destino, compression="snappy")
    
    return destino