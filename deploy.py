#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
  🚀 Script de Deploy MuleSoft: Exchange (v2) ➜ CloudHub 2.0
===============================================================================
  🎯 O que faz:
    1) Publica o artefato no **Anypoint Exchange** (executa `mvn clean deploy`)
       com testes **pulados por padrão**.
    2) Faz o **deploy no CloudHub 2.0** via `mvn mule:deploy` reaproveitando o
       artefato gerado.

  ✅ Requisitos:
    • Maven instalado no PATH (ou use --mvn-path) OU mvnw/mvnw.cmd no repo.
    • `settings.xml` apontando para o servidor do Exchange com credenciais
      de **Connected App** no formato `~~~Client~~~` / `client.id~?~client.secret`.
    • POM do projeto configurado (mule-maven-plugin + distributionManagement).

  🔐 Credenciais (Connected App):
    - Você pode **passar por flags** `--client-id` / `--client-secret`,
      **ou** usar as env vars ANYPOINT_CLIENT_ID / ANYPOINT_CLIENT_SECRET,
      **ou** usar os **defaults** chumbados abaixo (a pedido).

  🧪 Testes:
    - Por padrão, o script pula testes (`-DskipTests -DskipITs -DskipMunitTests`).
      Use `--no-skip-tests` para executar com testes.

  🔧 Overrides úteis (sem editar o POM):
    --env, --target, --business-group-id, --mule-version, --java-version,
    --release-channel, --server-id, --profiles

  📂 Logs:
    ./logs/01-exchange-deploy-*.log
    ./logs/02-cloudhub-deploy-*.log

  📌 Exemplos:
    python deploy-app.py --pom ./pom.xml --settings ./.maven/settings.xml \
      --client-id $ANYPOINT_CLIENT_ID --client-secret $ANYPOINT_CLIENT_SECRET

    python deploy-app.py --env dev --target Cloudhub-US-East-2 \
      --business-group-id 9d86053c-c394-4e52-b33c-029e02b59822

    # Rodar com testes
    python deploy-app.py --no-skip-tests
===============================================================================
"""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from typing import List

# ---------------------------------------------------------------------------
# Defaults solicitados (podem ser sobrescritos por flags/env)
# ---------------------------------------------------------------------------
DEFAULTS = {
    # 🔐 Credenciais Connected App (fallback se env vars não existirem)
    "CLIENT_ID": os.getenv("ANYPOINT_CLIENT_ID", "083d83056c5b4c08b2cfa523ce811c4c"),
    "CLIENT_SECRET": os.getenv("ANYPOINT_CLIENT_SECRET", "6e0D7191660746da958e6a50A11438F7"),

    # 🌎 Parâmetros de deploy
    "ENV": "dev",                              # environment (dev/qa/prod/Sandbox)
    "TARGET": "Cloudhub-US-East-2",           # região ou nome do Private Space
    "BG_ID": "9d86053c-c394-4e52-b33c-029e02b59822",  # Business Group ID
    "RELEASE_CHANNEL": "EDGE",                # EDGE | LTS | NONE
    "MULE_VERSION": "4.9.0",                  # runtime (ex.: 4.9.0)
    "JAVA_VERSION": "17",                     # 8 | 17
    "SERVER_ID": "Repository",                # id do <server> no settings.xml
    "PROFILES": "dev",                        # perfis Maven a ativar (-P)

    # 🧭 Caminhos padrão
    "POM": "./pom.xml",
    "SETTINGS": "./.maven/settings.xml",
}

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def resolve_maven(project_root: str, mvn_path_cli: str | None) -> str:
    """Resolve executável do Maven, priorizando mvnw/mvnw.cmd.
    Ordem: mvnw(.cmd) no repo ➜ --mvn-path ➜ mvn no PATH ➜ {MAVEN_HOME|M3_HOME}/bin/mvn(.cmd)
    """
    # 1) Wrapper local
    cand = os.path.join(project_root, "mvnw.cmd" if os.name == "nt" else "mvnw")
    if os.path.isfile(cand):
        return cand

    # 2) CLI
    if mvn_path_cli:
        if os.path.isfile(mvn_path_cli):
            return mvn_path_cli
        raise SystemExit(f"Maven não encontrado em --mvn-path: {mvn_path_cli}")

    # 3) PATH
    for name in (["mvn.cmd", "mvn"] if os.name == "nt" else ["mvn"]):
        found = shutil.which(name)
        if found:
            return found

    # 4) Variáveis de ambiente
    for env in ("MAVEN_HOME", "M3_HOME"):
        base = os.getenv(env)
        if base:
            exe = os.path.join(base, "bin", "mvn.cmd" if os.name == "nt" else "mvn")
            if os.path.isfile(exe):
                return exe

    raise SystemExit(
        "Maven não encontrado.\n"
        "- Opções:\n"
        "  a) Adicione Maven ao PATH (mvn/mvn.cmd)\n"
        "  b) Use o Wrapper (mvnw/mvnw.cmd) na raiz do repositório\n"
        "  c) Passe --mvn-path C:/caminho/para/mvn.cmd"
    )


def ensure_file(path: str, label: str) -> None:
    if not path:
        raise SystemExit(f"Caminho não informado: {label}")
    if not os.path.isfile(path):
        raise SystemExit(f"Arquivo não encontrado: {label} -> {path}")


def run(cmd: List[str], cwd: str, log_path: str, title: str, echo: bool = True) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    if echo:
        print("\n====== " + title + " ======")
        print(" ", " ".join(cmd))
    with open(log_path, "w", encoding="utf-8", errors="ignore") as lf:
        rc = subprocess.call(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT, text=True)
    with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
        tail = lf.readlines()[-120:]
    print("".join(tail))
    if rc != 0:
        raise SystemExit(f"[ERRO] Comando falhou. Veja o log: {log_path}")


# ---------------------------------------------------------------------------
# Montagem de comandos Maven
# ---------------------------------------------------------------------------

def base_mvn_args(
    mvn: str,
    settings: str | None,
    client_id: str,
    client_secret: str,
    profiles: str | None,
    pom: str | None,
    batch: bool = True,
) -> List[str]:
    args = [mvn]
    if batch:
        args += ["-B"]
    # Força update pra evitar cache "present, but unavailable"
    args += ["-U"]
    if settings:
        args += ["-s", settings]
    if profiles:
        args += ["-P", profiles]
    if pom:
        args += ["-f", pom]
    # Credenciais Connected App injetadas para o settings.xml
    args += [f"-Dclient.id={client_id}", f"-Dclient.secret={client_secret}"]
    return args


def add_common_overrides(
    cmd: List[str],
    env: str | None,
    target: str | None,
    bg_id: str | None,
    mule_version: str | None,
    java_version: str | None,
    release_channel: str | None,
    server_id: str | None,
) -> None:
    if env:
        cmd += [f"-Denv={env}", f"-Denvironment={env}"]
    if target:
        # Mule plugin aceita tanto target quanto region em alguns contextos
        cmd += [f"-Dtarget={target}", f"-Dregion={target}"]
    if bg_id:
        cmd += [f"-DbusinessGroupId={bg_id}"]
    if mule_version:
        cmd += [f"-Dapp.runtime={mule_version}", f"-DmuleVersion={mule_version}"]
    if java_version:
        cmd += [f"-Djava.version={java_version}"]
    if release_channel:
        cmd += [f"-DreleaseChannel={release_channel}"]
    if server_id:
        # Alguns POMs usam <server>${serverId}</server>
        cmd += [f"-DserverId={server_id}", f"-Dserver={server_id}"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publica no Exchange e depois deploya no CloudHub 2.0",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Caminhos
    parser.add_argument("--pom", default=DEFAULTS["POM"], help="Caminho do pom.xml do projeto")
    parser.add_argument("--settings", default=DEFAULTS["SETTINGS"], help="Caminho do settings.xml")
    parser.add_argument("--mvn-path", default=None, help="Caminho do mvn/mvn.cmd (se não estiver no PATH)")

    # Credenciais (Connected App)
    parser.add_argument("--client-id", default=DEFAULTS["CLIENT_ID"], help="Client ID do Connected App")
    parser.add_argument("--client-secret", default=DEFAULTS["CLIENT_SECRET"], help="Client Secret do Connected App")

    # Overrides de deploy
    parser.add_argument("--env", dest="env", default=DEFAULTS["ENV"], help="Environment do Anypoint (ex.: dev, qa, prod, Sandbox)")
    parser.add_argument("--target", dest="target", default=DEFAULTS["TARGET"], help="Target CloudHub 2.0 (ex.: Cloudhub-US-East-2 ou nome do Private Space)")
    parser.add_argument("--business-group-id", dest="bg_id", default=DEFAULTS["BG_ID"], help="Business Group ID (GUID)")
    parser.add_argument("--mule-version", dest="mule_version", default=DEFAULTS["MULE_VERSION"], help="Versão do Mule (ex.: 4.9.0)")
    parser.add_argument("--java-version", dest="java_version", default=DEFAULTS["JAVA_VERSION"], help="Versão do Java (8 ou 17)")
    parser.add_argument("--release-channel", dest="release_channel", default=DEFAULTS["RELEASE_CHANNEL"], help="Canal de release (EDGE, LTS, NONE)")
    parser.add_argument("--server-id", dest="server_id", default=DEFAULTS["SERVER_ID"], help="ID do <server> no settings.xml")
    parser.add_argument("--profiles", dest="profiles", default=DEFAULTS["PROFILES"], help="Perfis Maven a ativar (-P)")

    # Flags
    parser.add_argument("--no-skip-tests", action="store_true", help="Não pular testes (por padrão os testes são pulados)")
    parser.add_argument("--debug", action="store_true", help="Adiciona -X ao Maven para logs detalhados")
    parser.add_argument("--dry-run", action="store_true", help="Mostra comandos sem executar")

    args = parser.parse_args()

    project_root = os.path.abspath(os.path.dirname(args.pom))
    mvn = resolve_maven(project_root, args.mvn_path)

    ensure_file(args.pom, "pom.xml")
    if args.settings:
        ensure_file(args.settings, "settings.xml")

    # Credenciais obrigatórias
    if not args.client_id or not args.client_secret:
        raise SystemExit(
            "Client ID/Secret não informados.\n"
            "  Passe --client-id e --client-secret, ou\n"
            "  defina ANYPOINT_CLIENT_ID / ANYPOINT_CLIENT_SECRET."
        )

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    logs_dir = os.path.join(project_root, "logs")

    # Comum a todos os comandos Maven
    common = base_mvn_args(
        mvn=mvn,
        settings=args.settings,
        client_id=args.client_id,
        client_secret=args.client_secret,
        profiles=args.profiles,
        pom=args.pom,
    )

    if args.debug:
        common.append("-X")

    # 0) Go-offline (opcional, mas ajuda no cache)
    cmd_offline = common + ["dependency:go-offline"]

    # 1) Publica no Exchange (deploy de repositório)
    cmd_exchange = common + ["clean", "deploy"]
    if not args.no_skip_tests:
        cmd_exchange += ["-DskipTests", "-DskipITs", "-DskipMunitTests"]

    # 2) Deploy no CloudHub 2.0 (sem rebuild do artefato)
    cmd_cloudhub = common + ["mule:deploy"]
    add_common_overrides(
        cmd_cloudhub,
        env=args.env,
        target=args.target,
        bg_id=args.bg_id,
        mule_version=args.mule_version,
        java_version=args.java_version,
        release_channel=args.release_channel,
        server_id=args.server_id,
    )

    # Mostrar comandos
    print("============================================================")
    print("Deploy MuleSoft: Exchange ➜ CloudHub 2.0")
    print(f"Projeto : {args.pom}")
    print(f"Maven   : {mvn}")
    print(f"Settings: {args.settings or '(padrão Maven)'}")
    print(f"Env     : {args.env} | Target: {args.target} | BG: {args.bg_id}")
    print(f"Runtime : Mule {args.mule_version} / Java {args.java_version} / {args.release_channel}")
    print(f"Server  : {args.server_id} | Profiles: {args.profiles}")
    print(f"Logs    : {logs_dir}")
    print("============================================================")

    if args.dry_run:
        print("DRY-RUN ▶ Comandos que seriam executados:\n")
        print("[0] go-offline:\n  ", " ".join(cmd_offline))
        print("\n[1] exchange (deploy):\n  ", " ".join(cmd_exchange))
        print("\n[2] cloudhub (mule:deploy):\n  ", " ".join(cmd_cloudhub))
        return

    # Execução com logs
    try:
        run(cmd_offline, cwd=project_root, log_path=os.path.join(logs_dir, f"00-go-offline-{ts}.log"), title="[PREP] Go-offline", echo=True)
    except SystemExit as e:
        # Go-offline é auxiliar — não é fatal
        print(f"[AVISO] go-offline falhou: {e}. Continuando…")

    run(cmd_exchange, cwd=project_root, log_path=os.path.join(logs_dir, f"01-exchange-deploy-{ts}.log"), title="[1/2] Exchange: clean deploy")
    run(cmd_cloudhub, cwd=project_root, log_path=os.path.join(logs_dir, f"02-cloudhub-deploy-{ts}.log"), title="[2/2] CloudHub 2.0: mule:deploy")

    print("\n====== ✅ Concluído com sucesso. ======")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
