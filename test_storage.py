from test_api import get_token, get_states
from schema import parse_states
from storage import escribir_snapshot

BBOX = (48.0, 55.0, 2.0, 12.0)

token = get_token()
playload = get_states(token, BBOX)
rows = parse_states(playload)

destino = escribir_snapshot(rows)
print(f"Filas: {len(rows)}")
print(f"Escrito en: {destino}")
print(f"Tamano: {destino.stat().st_size / 1024:.1f} KB")