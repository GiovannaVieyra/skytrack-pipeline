from dotenv import load_dotenv
load_dotenv()

from test_api import get_token, get_states
from schema import parse_states
from storage import escribir_snapshot_r2

BBOX = (48.0, 55.0, 2.0, 12.0)

token = get_token()
payload = get_states(token, BBOX)
rows = parse_states(payload)

key = escribir_snapshot_r2(rows)
print(f"Filas: {len(rows)}")
print(f"Subido a R2: {key}")