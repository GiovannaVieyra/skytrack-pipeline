import os
import  requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
API_URL = "https://opensky-network.org/api/states/all"

BBOXES = {
    "chico (Holanda)": (50.5, 53.5, 3.5, 7.5),
    "mediano (Benelux+DE)": (48.0, 55.0, 2.0, 12.0),
    "grande (Europa occ.)": (43.0, 58.0, -5.0, 18.0),
}

def get_token():
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
    return r.json()["access_token"]

def medir(token, nombre, bbox):
    lamin, lamax, lomin, lomax = bbox
    r = requests.get(
        API_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"lamin": lamin, "lamax": lamax, "lomin": lomin, "lomax": lomax},
        timeout=60,
    )
    r.raise_for_status()
    
    restantes = r.headers.get("X-Rate-Limit-Remaining")
    aviones = len(r.json().get("states") or [])
    peso_kb = len(r.content) / 1024
    
    print(f"{nombre:24s} | aviones: {aviones:5d} | "
            f"respuesta: {peso_kb:7.1f} KB | creditos restantes: {restantes}")
    
    return restantes 

if __name__ == "__main__":
    token = get_token()
    print("Headers de la primera respuesta (para ver que devuelve OpenSky):\n")
    
    anterior = None
    for nombre, bbox in BBOXES.items():
        actual = medir(token, nombre, bbox)
        
        if anterior is not None and actual is not None:
            print(f"{'':24s} -> costo de la llamada anterior: {int(anterior) - int(actual)}\n")
        anterior = actual
        
        