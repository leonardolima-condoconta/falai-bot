#!/usr/bin/env python3
"""Gera Excel com todos os colaboradores, tipo de vinculo (CLT/PJ/Cooperado)
e dias presenciais na semana, a partir da API Convenia."""
import httpx, json, time, collections, sys

API_KEY_FILE = "/opt/data/convenia_data/.env"
BASE_URL = "https://public-api.convenia.com.br"
OUTPUT = "/opt/data/vinculo_presencial_colaboradores.xlsx"

def load_api_key():
    with open(API_KEY_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("CONVENIA_API_KEY="):
                return line.split("=", 1)[1]
    raise RuntimeError("CONVENIA_API_KEY nao encontrada")

HEADERS = {
    "token": None,
    "Accept": "application/json",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
}

def classify(cnpj, matricula):
    """Retorna (tipo_vinculo, observacao). Prioriza PJ > Cooperado > CLT."""
    has_cnpj = bool(cnpj and str(cnpj).strip())
    has_mat = bool(matricula and str(matricula).strip())
    if has_cnpj and has_mat:
        return "PJ", "Possui CNPJ E matricula cooperativa (classificado como PJ)"
    if has_cnpj:
        return "PJ", ""
    if has_mat:
        return "Cooperado", ""
    return "CLT", ""

def main():
    api_key = load_api_key()
    HEADERS["token"] = api_key

    rows = []
    stats = collections.Counter()

    with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=30,
                      follow_redirects=True) as client:
        r = client.get("/api/v3/employees", params={"status": "active", "limit": 500})
        if r.status_code != 200:
            print(f"ERRO lista: {r.status_code} {r.text[:200]}", file=sys.stderr)
            sys.exit(1)
        employees = r.json()["data"]
        total = len(employees)
        print(f"Colaboradores ativos: {total}")

        for i, emp in enumerate(employees):
            eid = emp["id"]
            name = emp.get("name", "")
            last_name = emp.get("last_name", "")
            email = emp.get("email", "")
            dept = (emp.get("department") or {}).get("name", "")
            job = (emp.get("job") or {}).get("name", "")

            cnpj = ""
            matricula = ""
            dias_pres = ""

            rd = client.get(f"/api/v3/employees/{eid}")
            if rd.status_code == 200:
                cfs = rd.json()["data"].get("custom_fields", [])
                for cf in cfs:
                    nm = cf.get("name", "")
                    val = cf.get("value") or ""
                    if nm == "CNPJ (quando PJ)":
                        cnpj = str(val).strip()
                    elif nm == "Matrícula Nova Cooperativa":
                        matricula = str(val).strip()
                    elif nm == "Dias Presenciais na Semana":
                        dias_pres = str(val).strip()

            tipo, obs = classify(cnpj, matricula)
            stats[tipo] += 1

            nome_completo = f"{name} {last_name}".strip()
            rows.append({
                "Nome": nome_completo,
                "Email": email,
                "Departamento": dept,
                "Cargo": job,
                "Tipo de Vínculo": tipo,
                "Matrícula Cooperativa": matricula,
                "CNPJ (quando PJ)": cnpj,
                "Dias Presenciais na Semana": dias_pres,
                "Observação": obs,
            })

            if (i + 1) % 25 == 0:
                print(f"  processados: {i+1}/{total}")
            time.sleep(1.2)  # rate limit 50/min

    # Ordenar por tipo e nome
    ordem = {"PJ": 0, "Cooperado": 1, "CLT": 2}
    rows.sort(key=lambda x: (ordem.get(x["Tipo de Vínculo"], 9), x["Nome"].lower()))

    # Gerar Excel
    import pandas as pd
    df = pd.DataFrame(rows)

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Colaboradores")

        # Sheet resumo
        resumo = pd.DataFrame([
            {"Métrica": "Total colaboradores ativos", "Valor": total},
            {"Métrica": "CLT", "Valor": stats.get("CLT", 0)},
            {"Métrica": "Cooperado", "Valor": stats.get("Cooperado", 0)},
            {"Métrica": "PJ", "Valor": stats.get("PJ", 0)},
        ])
        resumo.to_excel(writer, index=False, sheet_name="Resumo")

        # Ajustar largura das colunas
        for ws in writer.sheets.values():
            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        max_len = max(max_len, len(str(cell.value)))
                    except Exception:
                        pass
                ws.column_dimensions[col_letter].width = min(max_len + 2, 50)

    print(f"\n=== RESULTADO ===")
    print(f"Total: {total}")
    for k in ["CLT", "Cooperado", "PJ"]:
        print(f"  {k}: {stats.get(k, 0)}")
    print(f"\nExcel gerado: {OUTPUT}")

if __name__ == "__main__":
    main()
