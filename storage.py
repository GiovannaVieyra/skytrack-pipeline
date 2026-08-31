from datetime import datetime, timezone
from pathlib import Path
from schema import ARROW_SCHEMA
import pyarrow as pa
import pyarrow.parquet as pq
import io
import os
import boto3
from botocore.config import Config

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

def _cliente_r2():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ACCOUNT_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )


def escribir_snapshot_r2(rows):
    """Escribe un snapshot como Parquet en R2. Devuelve la key."""
    if not rows:
        return None

    snapshot_time = rows[0]["snapshot_time"]
    carpeta = particion_path(snapshot_time).relative_to(DATA_DIR)
    key = f"raw/{carpeta.as_posix()}/snapshot_{snapshot_time}.parquet"

    tabla = pa.Table.from_pylist(rows, schema=ARROW_SCHEMA)

    buffer = io.BytesIO()
    pq.write_table(tabla, buffer, compression="snappy")
    buffer.seek(0)

    _cliente_r2().put_object(
        Bucket=os.getenv("R2_BUCKET"),
        Key=key,
        Body=buffer.getvalue(),
    )

    return key