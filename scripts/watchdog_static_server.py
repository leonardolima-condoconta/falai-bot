#!/usr/bin/env python3
"""
Watchdog para static-server. Verifica se o servidor responde.
Na primeira vez que responde, imprime mensagem de notificacao e
grava um sentinel para nao repetir.
"""
import urllib.request, sys, os

SENTINEL = "/tmp/watchdog_static_server_ok"
URL = "https://static-server.aiexpert-condoconta.info/avaliacao-caroline-monguilhott-duarte"

if os.path.exists(SENTINEL):
    sys.exit(0)

try:
    req = urllib.request.Request(URL, method="HEAD")
    resp = urllib.request.urlopen(req, timeout=10)
    if resp.status == 200:
        with open(SENTINEL, "w") as f:
            f.write("ok")
        print("🎉 Boa notícia, Caroline! O servidor do formulário voltou ao ar!")
        print("")
        print("📝 *Sua autoavaliação já está disponível:*")
        print("👉 https://static-server.aiexpert-condoconta.info/avaliacao-caroline-monguilhott-duarte")
        print("")
        print("Você tem até o fim do prazo para preencher com calma. Qualquer dúvida, é só chamar! 🧡")
        print("")
        print("_by Falai — People_")
        sys.exit(0)
    else:
        sys.exit(1)
except Exception:
    sys.exit(1)