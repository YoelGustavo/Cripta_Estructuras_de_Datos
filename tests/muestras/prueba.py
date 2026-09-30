# explorar_api.py — script desechable, solo para conocer los datos
#NO USAR
#USELESS
import json, uuid, requests
from pathlib import Path

BASE = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
HEADERS = {"X-Cripta-Client-Id": str(uuid.uuid4())}  # uno por ejecución
CARPETA = Path("tests/muestras")
CARPETA.mkdir(parents=True, exist_ok=True)

def pedir(ruta, nombre):
    r = requests.get(BASE + ruta, headers=HEADERS, timeout=10)
    print(r.status_code, ruta)
    r.raise_for_status()
    texto = json.dumps(r.json(), ensure_ascii=False, indent=2)
    (CARPETA / nombre).write_text(texto, encoding="utf-8")
    return r.json()

criptas = pedir("/criptas", "criptas.json")
cid = criptas["criptas"][0]["id"]
pedir(f"/criptas/{cid}", f"{cid}_general.json")
pagina = pedir(f"/criptas/{cid}/salas?pagina=1", f"{cid}_salas_1.json")
ids = ",".join(str(s["id"]) for s in pagina["salas"][:10])
pedir(f"/criptas/{cid}/contenido?salas={ids}", f"{cid}_contenido_1.json")