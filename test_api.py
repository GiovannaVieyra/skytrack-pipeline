import os
import requests
from dotenv import load_dotenv


load_dotenv()

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
API_URL = "https://opensky-network.org/api/states/all"


def get_token():
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("OPENSKY_CLIENT_ID"),
            "client_secret": os.getenv("OPENSKY_CLIENT_SECRET"),
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_states(token, bbox):
    lamin, lamax, lomin, lomax = bbox
    response = requests.get(
        API_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"lamin": lamin, "lamax": lamax, "lomin": lomin, "lomax": lomax},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Bounding box chico sobre Países Bajos y oeste de Alemania
    BBOX = (50.5, 53.5, 3.5, 7.5)

    token = get_token()
    print("Token obtenido")

    data = get_states(token, BBOX)
    states = data.get("states") or []
    print(f"Timestamp: {data.get('time')}")
    print(f"Aviones en el bbox: {len(states)}\n")

    for state in states[:5]:
        icao24 = state[0]
        callsign = (state[1] or "").strip() or "sin callsign"
        pais = state[2]
        lon, lat = state[5], state[6]
        altitud = state[7]
        velocidad = state[9]
        print(f"{icao24} | {callsign:10s} | {pais:15s} | "
                f"lat {lat} lon {lon} | alt {altitud} m | vel {velocidad} m/s")
