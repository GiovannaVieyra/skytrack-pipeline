"""Worker de ingesta: pollea OpenSky y escribe snapshots crudos."""

import logging
import os
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from schema import parse_states
from storage import escribir_snapshot_r2

load_dotenv()

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
API_URL = "https://opensky-network.org/api/states/all"

BBOX = (48.0, 55.0, 2.0, 12.0)
INTERVALO = 75
TOKEN_MARGEN = timedelta(minutes=5)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler("worker.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("skytrack")


class TokenManager:
    """Guarda el token y lo renueva antes de que venza."""

    def __init__(self):
        self._token = None
        self._vence = datetime.now(timezone.utc)

    def get(self):
        if self._token is None or datetime.now(timezone.utc) >= self._vence - TOKEN_MARGEN:
            self._renovar()
        return self._token

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=60))
    def _renovar(self):
        log.info("Renovando token")
        try:
            r = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": os.getenv("OPENSKY_CLIENT_ID"),
                    "client_secret": os.getenv("OPENSKY_CLIENT_SECRET"),
                },
                timeout=30,
            )
            r.raise_for_status()
        except Exception as e:
            log.error("Fallo la renovacion del token: %s", e)
            raise
        payload = r.json()
        self._token = payload["access_token"]
        segundos = payload.get("expires_in", 1800)
        self._vence = datetime.now(timezone.utc) + timedelta(seconds=segundos)
        log.info("Token renovado, vence en %s segundos", segundos)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def pedir_estados(token):
    lamin, lamax, lomin, lomax = BBOX
    r = requests.get(
        API_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"lamin": lamin, "lamax": lamax, "lomin": lomin, "lomax": lomax},
        timeout=45,
    )
    r.raise_for_status()
    return r.json(), r.headers.get("X-Rate-Limit-Remaining")


def main():
    faltantes = [v for v in (
        "OPENSKY_CLIENT_ID", "OPENSKY_CLIENT_SECRET",
        "R2_ACCOUNT_ENDPOINT", "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY", "R2_BUCKET",
    ) if not os.getenv(v)]
    if faltantes:
        log.error("Faltan variables de entorno: %s", ", ".join(faltantes))
        raise SystemExit(1)

    try:
        prueba = requests.get(
            "https://opensky-network.org/api/states/all?lamin=51&lamax=52&lomin=4&lomax=5",
            timeout=20,
        )
        log.info("Prueba de conectividad: HTTP %s", prueba.status_code)
    except Exception as e:
        log.error("Prueba de conectividad fallo: %s", e)

    log.info("Worker iniciado | bbox=%s | intervalo=%ss", BBOX, INTERVALO)
    tokens = TokenManager()
    ciclos = 0
    fallas = 0

    while True:
        inicio = time.monotonic()
        ciclos += 1

        try:
            payload, creditos = pedir_estados(tokens.get())
            rows = parse_states(payload)

            if not rows:
                log.warning("Snapshot vacio, no se escribe nada")
            else:
                destino = escribir_snapshot_r2(rows)
                log.info(
                    "Ciclo %d | %d aviones | creditos: %s | %s",
                    ciclos, len(rows), creditos, destino,
                )

        except Exception as e:
            fallas += 1
            log.error("Ciclo %d fallo (%d fallas totales): %s", ciclos, fallas, e)

        transcurrido = time.monotonic() - inicio
        espera = max(0, INTERVALO - transcurrido)
        if espera == 0:
            log.warning("El ciclo tardo %.1fs, mas que el intervalo", transcurrido)
        time.sleep(espera)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Worker detenido por el usuario")