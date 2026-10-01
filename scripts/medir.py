#!/usr/bin/env python3
"""Roda os experimentos e grava dados/medicoes.csv.

Uso:
    python3 scripts/medir.py                  # bateria completa
    python3 scripts/medir.py --rapido         # bateria reduzida
"""
import argparse
import csv
import os
import platform
import re
import statistics
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(RAIZ, "bin")
SAIDA = os.path.join(RAIZ, "dados", "medicoes.csv")

RE_CHECK = re.compile(r"checksum=(-?\d+)")
RE_TEMPO = re.compile(r"tempo=([\d.]+)")
RE_CALC = re.compile(r"t_calc_max=([\d.]+)")
RE_COM = re.compile(r"t_comunicacao=([\d.]+)")
RE_DESB = re.compile(r"desbalanceamento=([\d.]+)")


def executa(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FALHOU:", " ".join(cmd), file=sys.stderr)
        print(r.stderr, file=sys.stderr)
        sys.exit(1)
    s = r.stdout
    return {
        "checksum": int(RE_CHECK.search(s).group(1)),
        "tempo": float(RE_TEMPO.search(s).group(1)),
        "t_calc": float(RE_CALC.search(s).group(1)) if RE_CALC.search(s) else "",
        "t_com": float(RE_COM.search(s).group(1)) if RE_COM.search(s) else "",
        "desbal": float(RE_DESB.search(s).group(1)) if RE_DESB.search(s) else "",
    }


def mede(cmd, reps):
    executa(cmd)  # aquecimento, descartado
    amostras = [executa(cmd) for _ in range(reps)]
    tempos = [a["tempo"] for a in amostras]
    base = amostras[0]
    base["tempo"] = statistics.median(tempos)
    base["tempo_min"] = min(tempos)
    base["tempo_max"] = max(tempos)
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args()

    nucleos = os.cpu_count()
    if args.rapido:
        tamanhos = [(800, 800), (1200, 1200)]
        threads = [t for t in (1, 2, 4, nucleos) if t <= nucleos]
        procs = [p for p in (1, 2, 4) if p <= nucleos]
        politicas = ["static", "dynamic"]
    else:
        tamanhos = [(600, 600), (1000, 1000), (1600, 1600), (2200, 2200)]
        threads = sorted({t for t in (1, 2, 4, 6, 8, nucleos) if t <= nucleos})
        procs = sorted({p for p in (1, 2, 4, 6, 8, nucleos) if p <= nucleos})
        politicas = ["static", "dynamic", "guided"]

    threads = sorted(set(threads))
    maior = tamanhos[-1]
    linhas = []

    def add(**kw):
        kw.setdefault("maquina", platform.node())
        kw.setdefault("nucleos", nucleos)
        linhas.append(kw)
        print("  ".join(f"{k}={v}" for k, v in kw.items() if k in
                        ("versao", "W", "config", "n", "tempo", "checksum")))

    print("== baseline sequencial ==")
    base_por_tam = {}
    for W, H in tamanhos:
        r = mede([f"{BIN}/mandelbrot_seq", str(W), str(H)], args.reps)
        base_por_tam[(W, H)] = r["tempo"]
        add(versao="sequencial", W=W, H=H, config="-", n=1, **r)

    print("== OpenMP: speedup por threads (schedule dynamic) ==")
    for W, H in tamanhos:
        for t in threads:
            r = mede([f"{BIN}/mandelbrot_omp", str(W), str(H), str(t),
                      "dynamic", "1", "reduction"], args.reps)
            add(versao="openmp", W=W, H=H, config="dynamic,1,reduction", n=t,
                speedup=base_por_tam[(W, H)] / r["tempo"],
                eficiencia=base_por_tam[(W, H)] / r["tempo"] / t, **r)

    print("== OpenMP: comparacao de politicas de escalonamento ==")
    for pol in politicas:
        for chunk in (1, 10, 0):
            for t in threads:
                if t == 1:
                    continue
                r = mede([f"{BIN}/mandelbrot_omp", *map(str, maior), str(t),
                          pol, str(chunk), "reduction"], args.reps)
                add(versao="openmp_politica", W=maior[0], H=maior[1],
                    config=f"{pol},{chunk}", n=t,
                    speedup=base_por_tam[maior] / r["tempo"], **r)

    print("== OpenMP: reducao critical vs atomic vs reduction ==")
    for red in ("reduction", "atomic", "critical"):
        r = mede([f"{BIN}/mandelbrot_omp", *map(str, maior), str(max(threads)),
                  "dynamic", "1", red], args.reps)
        add(versao="openmp_reducao", W=maior[0], H=maior[1], config=red,
            n=max(threads), **r)

    print("== MPI: speedup por processos ==")
    for W, H in tamanhos:
        for dec in ("bloco", "ciclico"):
            for p in procs:
                r = mede(["mpirun", "--oversubscribe", "-np", str(p),
                          f"{BIN}/mandelbrot_mpi", str(W), str(H), dec], args.reps)
                add(versao="mpi", W=W, H=H, config=dec, n=p,
                    speedup=base_por_tam[(W, H)] / r["tempo"],
                    eficiencia=base_por_tam[(W, H)] / r["tempo"] / p, **r)

    print("== escalabilidade fraca (carga por unidade constante) ==")
    lado0 = 800
    for p in procs:
        lado = int(round(lado0 * (p ** 0.5)))
        r = mede(["mpirun", "--oversubscribe", "-np", str(p),
                  f"{BIN}/mandelbrot_mpi", str(lado), str(lado), "ciclico"], args.reps)
        add(versao="mpi_fraca", W=lado, H=lado, config="ciclico", n=p, **r)
    for t in threads:
        lado = int(round(lado0 * (t ** 0.5)))
        r = mede([f"{BIN}/mandelbrot_omp", str(lado), str(lado), str(t),
                  "dynamic", "1", "reduction"], args.reps)
        add(versao="openmp_fraca", W=lado, H=lado, config="dynamic,1", n=t, **r)

    campos = sorted({k for l in linhas for k in l})
    ordem = ["versao", "maquina", "nucleos", "W", "H", "config", "n", "tempo",
             "tempo_min", "tempo_max", "speedup", "eficiencia", "t_calc",
             "t_com", "desbal", "checksum"]
    campos = [c for c in ordem if c in campos] + [c for c in campos if c not in ordem]
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)

    refs = {(l["W"], l["H"]): l["checksum"] for l in linhas if l["versao"] == "sequencial"}
    erros = [l for l in linhas if refs.get((l["W"], l["H"])) not in (None, l["checksum"])]
    print(f"\nCSV gravado em {SAIDA} ({len(linhas)} linhas)")
    print("VALIDACAO DE CORRETUDE:",
          "OK — todos os checksums batem com o baseline" if not erros
          else f"FALHOU em {len(erros)} execucoes")


if __name__ == "__main__":
    main()
