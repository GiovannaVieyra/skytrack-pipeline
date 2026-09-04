"""Exploracion inicial de los snapshots crudos en R2."""

import os 
import duckdb
from dotenv import load_dotenv

load_dotenv()

con = duckdb.connect()
endpoint = os.getenv("R2_ACCOUNT_ENDPOINT").replace("https://", "")

con.execute(f"""
    INSTALL httpfs;
    LOAD httpfs;
    SET s3_endpoint = '{endpoint}';
    SET s3_access_key_id = '{os.getenv("R2_ACCESS_KEY_ID")}';
    SET s3_secret_access_key = '{os.getenv("R2_SECRET_ACCESS_KEY")}';
    SET s3_url_style = 'path';
    SET s3_region = 'auto';
""")

BUCKET = os.getenv("R2_BUCKET")
FUENTE = f"s3://{BUCKET}/raw/**/*.parquet"

print("Leyendo snapshots desde R2...\n")

resumen = con.execute(f"""
    SELECT
        COUNT(*) AS posiciones,
        COUNT(DISTINCT icao24) AS aviones_unicos,
        COUNT(DISTINCT snapshot_time) AS snapshots,
        MIN(to_timestamp(snapshot_time)) AS desde,
        MAX(to_timestamp(snapshot_time)) AS hasta
    FROM read_parquet('{FUENTE}')
""").fetchone()

print(f"Posiciones totales : {resumen[0]:,}")
print(f"Aviones unicos     : {resumen[1]:,}")
print(f"Snapshots          : {resumen[2]:,}")
print(f"Desde              : {resumen[3]}")
print(f"Hasta              : {resumen[4]}")

print("\n--- Aviones con mas posiciones registradas ---\n")

top = con.execute(f"""
    SELECT
        icao24,
        any_value(origin_country) AS pais,
        COUNT(*) AS posiciones,
        COUNT(DISTINCT callsign) AS callsigns,
        MIN(to_timestamp(snapshot_time)) AS primera,
        MAX(to_timestamp(snapshot_time)) AS ultima
    FROM read_parquet('{FUENTE}')
    GROUP BY icao24
    ORDER BY posiciones DESC
    LIMIT 10
""").fetchall()

for fila in top:
    print(f"{fila[0]} | {fila[1]:18s} | {fila[2]:5d} pos | {fila[3]:2d} callsigns | {fila[4]} -> {fila[5]}")
    
print("\n--- Trayectoria de 3b27ff (muestra) ---\n")

muestra = con.execute(f"""
    SELECT
        to_timestamp(snapshot_time) AS t,
        callsign,
        ROUND(latitude, 3) AS lat,
        ROUND(longitude, 3) AS lon,
        baro_altitude AS alt,
        ROUND(velocity) AS vel,
        on_ground
    FROM read_parquet('{FUENTE}')
    WHERE icao24 = '3b27ff'
    ORDER BY snapshot_time
    LIMIT 40
""").fetchall()

for f in muestra:
    print(f"{f[0]} | {str(f[1]):9s} | {f[2]:7.3f} {f[3]:7.3f} | alt {str(f[4]):8s} | vel {str(f[5]):6s} | tierra: {f[6]}")
    
    print("\n--- Cuanto ruido de tierra hay ---\n")

ruido = con.execute(f"""
    WITH por_avion AS (
        SELECT
            icao24,
            COUNT(*) AS posiciones,
            SUM(CASE WHEN on_ground THEN 1 ELSE 0 END) AS en_tierra,
            MAX(COALESCE(baro_altitude, 0)) AS alt_max
        FROM read_parquet('{FUENTE}')
        GROUP BY icao24
    )
    SELECT
        COUNT(*) FILTER (WHERE alt_max < 1000) AS aviones_nunca_volaron,
        COUNT(*) AS aviones_total,
        SUM(posiciones) FILTER (WHERE alt_max < 1000) AS posiciones_ruido,
        SUM(posiciones) AS posiciones_total
    FROM por_avion
""").fetchone()

print(f"Aviones que nunca superaron 1000m : {ruido[0]:,} de {ruido[1]:,}")
print(f"Posiciones que aportan            : {ruido[2]:,} de {ruido[3]:,}")