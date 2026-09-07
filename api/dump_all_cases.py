import json
import httpx
from pathlib import Path

BASE = "http://localhost:8000"
CASES_PATH = Path("../agent-input/cases.json")

cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
client = httpx.Client(headers={"x-user-id": "usr_001"})

def get(path, **params):
    try:
        r = client.get(f"{BASE}{path}", params=params)
        return r.json()
    except Exception as e:
        return {"erro": str(e)}

for case in cases:
    asset_id = case.get("asset_id")
    print("\n" + "=" * 90)
    print(f"{case['ticket_id']} ({case['id']}) — ativo: {asset_id}")
    print(f"Mensagem: {case['message']}")
    print("=" * 90)

    if not asset_id:
        print("(sem ativo associado — caso só de conhecimento)")
        continue

    asset = get(f"/assets/{asset_id}")
    print(f"\n[asset]        mode={asset.get('mode')}  data={json.dumps(asset.get('data'), ensure_ascii=False)[:200]}")

    analyses = get(f"/assets/{asset_id}/analyses")
    print(f"[analyses]     mode={analyses.get('mode')}  n={len(analyses.get('data', {}).get('analyses', []) or [])}")

    baseline = get(f"/assets/{asset_id}/baseline")
    print(f"[baseline]     mode={baseline.get('mode')}  state={baseline.get('data', {}).get('state')}")

    rms = get(f"/assets/{asset_id}/rms")
    print(f"[rms]          mode={rms.get('mode')}")

    dq = get(f"/assets/{asset_id}/data-quality")
    print(f"[data_quality] mode={dq.get('mode')}")

client.close()
print("\nOK — todos os casos percorridos.")