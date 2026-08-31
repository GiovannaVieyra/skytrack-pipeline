from dotenv import load_dotenv
from schema import parse_states
from test_api import get_token, get_states

load_dotenv()

BBOX = (48.0, 55.0, 2.0, 12.0)

token = get_token()
playload = get_states(token, BBOX)
rows = parse_states(playload)

print(f"Filas parseadas: {len(rows)}\n")

for row in rows[:2]:
    for k, v in row.items():
        print(f" {k:18s}: {v}")
    print()