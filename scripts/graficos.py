#!/usr/bin/env python3
"""Gera os graficos a partir de dados/medicoes.csv em dados/graficos/."""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, "dados", "medicoes.csv")
DEST = os.path.join(RAIZ, "dados", "graficos")


def carregar():
    with open(CSV) as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def salvar(nome):
    os.makedirs(DEST, exist_ok=True)
    plt.tight_layout()
    plt.savefig(os.path.join(DEST, nome), dpi=150)
    plt.close()
    print("gerado:", nome)


def curva_speedup(linhas, versao, titulo, arquivo, eixo):
    grupos = defaultdict(list)
    for l in linhas:
        if l["versao"] != versao or not num(l.get("speedup")):
            continue
        grupos[f'{l["W"]}x{l["H"]} {l["config"]}'].append((int(l["n"]), num(l["speedup"])))
    if not grupos:
        return
    plt.figure(figsize=(7, 5))
    maxn = 1
    for rot, pts in sorted(grupos.items()):
        pts.sort()
        maxn = max(maxn, pts[-1][0])
        plt.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", label=rot)
    plt.plot([1, maxn], [1, maxn], "k--", linewidth=1, label="ideal (linear)")
    plt.xlabel(eixo); plt.ylabel("speedup sobre o baseline sequencial")
    plt.title(titulo); plt.grid(alpha=.3); plt.legend(fontsize=8)
    salvar(arquivo)


def curva_eficiencia(linhas, versao, titulo, arquivo, eixo):
    grupos = defaultdict(list)
    for l in linhas:
        if l["versao"] != versao or not num(l.get("eficiencia")):
            continue
        grupos[f'{l["W"]}x{l["H"]} {l["config"]}'].append((int(l["n"]), num(l["eficiencia"])))
    if not grupos:
        return
    plt.figure(figsize=(7, 5))
    for rot, pts in sorted(grupos.items()):
        pts.sort()
        plt.plot([p[0] for p in pts], [p[1] for p in pts], marker="s", label=rot)
    plt.axhline(1.0, color="k", linestyle="--", linewidth=1, label="ideal")
    plt.xlabel(eixo); plt.ylabel("eficiencia")
    plt.title(titulo); plt.grid(alpha=.3); plt.legend(fontsize=8)
    salvar(arquivo)


def politicas(linhas):
    grupos = defaultdict(list)
    for l in linhas:
        if l["versao"] != "openmp_politica":
            continue
        grupos[l["config"]].append((int(l["n"]), num(l["tempo"])))
    if not grupos:
        return
    plt.figure(figsize=(8, 5))
    for rot, pts in sorted(grupos.items()):
        pts.sort()
        plt.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", label=rot)
    plt.xlabel("threads"); plt.ylabel("tempo (s)")
    plt.title("OpenMP — politicas de escalonamento (schedule,chunk)")
    plt.grid(alpha=.3); plt.legend(fontsize=8, ncol=2)
    salvar("openmp_politicas.png")


def tempo_por_tamanho(linhas):
    grupos = defaultdict(list)
    for l in linhas:
        if l["versao"] != "sequencial":
            continue
        grupos["sequencial"].append((int(l["W"]), num(l["tempo"])))
    if not grupos:
        return
    plt.figure(figsize=(7, 5))
    for rot, pts in grupos.items():
        pts.sort()
        plt.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", label=rot)
    plt.xlabel("lado da imagem (pixels)"); plt.ylabel("tempo (s)")
    plt.title("Baseline sequencial — crescimento do tempo")
    plt.grid(alpha=.3); plt.legend()
    salvar("baseline_tempo.png")


def comunicacao(linhas):
    grupos = defaultdict(list)
    for l in linhas:
        if l["versao"] != "mpi" or not num(l.get("t_com")):
            continue
        grupos[f'{l["W"]}x{l["H"]} {l["config"]}'].append((int(l["n"]), num(l["t_com"])))
    if not grupos:
        return
    plt.figure(figsize=(7, 5))
    for rot, pts in sorted(grupos.items()):
        pts.sort()
        plt.plot([p[0] for p in pts], [p[1] for p in pts], marker="^", label=rot)
    plt.xlabel("processos"); plt.ylabel("tempo de comunicacao (s)")
    plt.title("MPI — overhead de comunicacao (Gatherv)")
    plt.grid(alpha=.3); plt.legend(fontsize=8)
    salvar("mpi_comunicacao.png")


def desbalanceamento(linhas):
    grupos = defaultdict(list)
    for l in linhas:
        if l["versao"] != "mpi" or not num(l.get("desbal")):
            continue
        grupos[l["config"]].append((int(l["n"]), num(l["desbal"])))
    if not grupos:
        return
    plt.figure(figsize=(7, 5))
    for rot, pts in sorted(grupos.items()):
        agreg = defaultdict(list)
        for n, v in pts:
            agreg[n].append(v)
        xs = sorted(agreg)
        plt.plot(xs, [sum(agreg[x]) / len(agreg[x]) for x in xs], marker="o", label=rot)
    plt.xlabel("processos"); plt.ylabel("desbalanceamento (%)")
    plt.title("MPI — desbalanceamento: bloco vs ciclico")
    plt.grid(alpha=.3); plt.legend()
    salvar("mpi_desbalanceamento.png")


def escalabilidade_fraca(linhas):
    plt.figure(figsize=(7, 5))
    achou = False
    for versao, rot in (("openmp_fraca", "OpenMP"), ("mpi_fraca", "MPI")):
        pts = sorted((int(l["n"]), num(l["tempo"])) for l in linhas if l["versao"] == versao)
        if not pts:
            continue
        achou = True
        t1 = pts[0][1]
        plt.plot([p[0] for p in pts], [t1 / p[1] for p in pts], marker="o", label=rot)
    if not achou:
        plt.close()
        return
    plt.axhline(1.0, color="k", linestyle="--", linewidth=1, label="ideal")
    plt.xlabel("unidades de processamento"); plt.ylabel("eficiencia fraca")
    plt.title("Escalabilidade fraca (carga por unidade constante)")
    plt.grid(alpha=.3); plt.legend()
    salvar("escalabilidade_fraca.png")


if __name__ == "__main__":
    linhas = carregar()
    tempo_por_tamanho(linhas)
    curva_speedup(linhas, "openmp", "OpenMP — speedup por threads", "openmp_speedup.png", "threads")
    curva_eficiencia(linhas, "openmp", "OpenMP — eficiencia", "openmp_eficiencia.png", "threads")
    curva_speedup(linhas, "mpi", "MPI — speedup por processos", "mpi_speedup.png", "processos")
    curva_eficiencia(linhas, "mpi", "MPI — eficiencia", "mpi_eficiencia.png", "processos")
    politicas(linhas)
    comunicacao(linhas)
    desbalanceamento(linhas)
    escalabilidade_fraca(linhas)
    print("\ngraficos em", DEST)
