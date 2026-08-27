#!/usr/bin/env python3
"""
Análise de turnover/headcount a partir dos backups SQLite do cadastro Convenia.

Roda de /opt/data com:
    /opt/data/.venv/bin/python3 skills/haas/falai-rbac/scripts/turnover_snapshot_diff.py

O que faz:
  1. Headcount total por snapshot (ativos/inativos) — linha do tempo
  2. Admissões e desligamentos via diff de snapshots consecutivos
  3. Headcount ativo por área (último backup)
  4. Admissões do ano por mês e por área (último backup)

Fonte: /opt/data/convenia_data/backups/convenia_YYYY-MM-DD.db
"""
import sqlite3, glob, os, sys
from collections import Counter, defaultdict

BACKUPS_DIR = "/opt/data/convenia_data/backups"
ANO = "2026"  # ano das admissões a reportar


def load(dbpath):
    db = sqlite3.connect(dbpath)
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    rows = cur.execute(
        "SELECT id, name, email, is_active, hiring_date, department_id FROM employees"
    ).fetchall()
    depts = {r["id"]: r["name"] for r in cur.execute("SELECT id, name FROM departments")}
    db.close()
    out = {}
    for r in rows:
        out[r["id"]] = dict(r, dept=depts.get(r["department_id"]))
    return out


def main():
    backups = sorted(glob.glob(os.path.join(BACKUPS_DIR, "convenia_*.db")))
    if not backups:
        print(f"Nenhum backup em {BACKUPS_DIR}")
        sys.exit(1)
    snaps = {}
    for b in backups:
        d = os.path.basename(b).replace("convenia_", "").replace(".db", "")
        snaps[d] = load(b)
    dates = sorted(snaps.keys())

    print("=== HEADCOUNT POR SNAPSHOT ===")
    for d in dates:
        rows = snaps[d]
        act = sum(1 for v in rows.values() if v["is_active"])
        ina = len(rows) - act
        print(f"{d}: total={len(rows)} ativos={act} inativos={ina}")

    print("\n=== ADMISSÕES / DESLIGAMENTOS (diff snapshots) ===")
    prev = None
    for d in dates:
        ids = set(snaps[d])
        if prev is not None:
            for i in ids - set(prev):
                r = snaps[d][i]
                print(f"{d}: +ADMISSAO {r['name']} | {r['email']} | hiring={r['hiring_date']} | dept={r['dept']}")
            for i in set(prev) - ids:
                r = prev[i]
                print(f"{d}: -REMOVIDO {r['name']} | {r['email']} | dept={r['dept']}")
            for i in ids & set(prev):
                a0, a1 = prev[i]["is_active"], snaps[d][i]["is_active"]
                if a0 != a1:
                    r = snaps[d][i]
                    print(f"{d}: FLIP is_active {r['name']} | {r['email']} | {a0}->{a1}")
        prev = snaps[d]

    latest = snaps[dates[-1]]
    active = [r for r in latest.values() if r["is_active"]]
    print(f"\n=== HEADCOUNT ATIVO POR ÁREA (último backup {dates[-1]}) ===")
    hc = Counter(r["dept"] for r in active)
    for dept, c in sorted(hc.items(), key=lambda x: -x[1]):
        print(f"{dept}: {c}")
    print(f"TOTAL ATIVOS: {len(active)}")

    print(f"\n=== ADMISSÕES {ANO} POR MÊS ===")
    monthly = Counter()
    for r in latest.values():
        hd = r["hiring_date"]
        if hd and hd.startswith(ANO):
            monthly[hd[:7]] += 1
    for m in sorted(monthly):
        print(f"{m}: {monthly[m]}")
    print(f"TOTAL {ANO}: {sum(monthly.values())}")

    print(f"\n=== ADMISSÕES {ANO} POR ÁREA ===")
    am = defaultdict(Counter)
    for r in latest.values():
        hd = r["hiring_date"]
        if hd and hd.startswith(ANO):
            am[r["dept"]][hd[:7]] += 1
    for dept in sorted(am):
        mm = am[dept]
        detail = ", ".join(f"{m[5:7]}:{mm[m]}" for m in sorted(mm))
        print(f"{dept} (total {sum(mm.values())}): {detail}")


if __name__ == "__main__":
    main()
