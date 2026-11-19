"""Desenha todas as chapas de uma solução salva (CSV de resultado + .solucao.csv).

Uso (na raiz do projeto; requer matplotlib):
    python3 docs/apresentacao/desenhar_solucao.py \
        results/ta_v1/calibration/congelada_v2/execucoes/A14__Hbase__1001 \
        --saida docs/apresentacao/img/solucao_A14.png [--colunas 10] [--nota "texto extra"]

O diretório da execução deve conter o CSV de resultado (com caminho_instancia, K e
LBref) e o arquivo .solucao.csv. Só desenha soluções marcadas como validadas.
"""
import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

AZUL, LARANJA = "#2a78d6", "#eb6834"
TEXTO, TEXTO2, FUNDO = "#0b0b0b", "#52514e", "#f4f3ef"

args = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
args.add_argument("execucao", type=Path, help="diretório da execução")
args.add_argument("--saida", type=Path, required=True)
args.add_argument("--colunas", type=int)
args.add_argument("--nota", default="", help="linha extra abaixo do título")
a = args.parse_args()

resultado = next(f for f in a.execucao.glob("*.csv") if not f.name.endswith(".solucao.csv"))
r = next(csv.DictReader(open(resultado, encoding="utf-8")))
assert r["validada"] == "1", "solução não validada"
pecas = list(csv.DictReader(open(next(a.execucao.glob("*.solucao.csv")), encoding="utf-8")))
caminho = Path(r["caminho_instancia"])
if not caminho.exists():  # execução feita em outra máquina: procura pelo nome em instances/source/
    raiz = Path(__file__).resolve().parents[2] / "instances/source"
    achados = list(raiz.rglob(caminho.name))
    assert len(achados) == 1, f"instância {caminho.name} não encontrada (ou ambígua) em {raiz}"
    caminho = achados[0]
W, H = map(int, open(caminho).read().split()[1:3])
chapas = sorted({int(p["chapa"]) for p in pecas})
assert len(chapas) == int(r["K"])

n = len(chapas)
colunas = a.colunas or min(10, max(3, math.ceil(math.sqrt(n * 1.5))))
linhas = math.ceil(n / colunas)
grande = n > 20  # muitas chapas: rótulos menores e sem "ocupada"
lado = 1.6 if grande else 3.0
fig, eixos = plt.subplots(linhas, colunas, figsize=(lado * colunas, (lado * H / W + (0.35 if grande else 0.6)) * linhas))
eixos = list(getattr(eixos, "ravel", lambda: [eixos])())
for ax in eixos:
    ax.axis("off")

area_total = 0
for c in chapas:
    ax = eixos[c]
    ax.add_patch(Rectangle((0, 0), W, H, facecolor=FUNDO, edgecolor=TEXTO2, linewidth=0.8 if grande else 1.2))
    area = 0
    for p in (p for p in pecas if int(p["chapa"]) == c):
        x, y, w, h = (int(p[k]) for k in ("x", "y", "largura", "altura"))
        area += w * h
        ax.add_patch(Rectangle((x, y), w, h, facecolor=LARANJA if p["rotacionada"] == "1" else AZUL,
                               edgecolor="white", linewidth=0.6 if grande else 1.5, alpha=0.85))
    area_total += area
    ax.set_xlim(-W * 0.02, W * 1.02)
    ax.set_ylim(-H * 0.02, H * 1.02)
    ax.set_aspect("equal")
    ocup = "100%" if area == W * H else f"{int(1000 * area / (W * H)) / 10:.1f}%".replace(".", ",")
    ax.set_title(f"{c + 1} · {ocup}" if grande else f"Chapa {c + 1} — {ocup} ocupada",
                 fontsize=8 if grande else 11, color=TEXTO2, pad=2 if grande else 6)

media = f"{int(1000 * area_total / (W * H * n)) / 10:.1f}%".replace(".", ",")
titulo = (f"{r['instancia']} · {r['metodo']} · K = {n} (LBref = {r['LBref']}) · {len(pecas)} peças · "
          f"ocupação média {media}")
altura = fig.get_size_inches()[1]
topo = 1 - (0.95 if a.nota else 0.6) / altura  # espaço do título (e da nota) em polegadas
fig.text(0.01, 1 - 0.1 / altura, titulo, fontsize=16 if grande else 15, fontweight="bold", va="top", ha="left")
if a.nota:
    fig.text(0.01, 1 - 0.5 / altura, a.nota, fontsize=13, color=TEXTO2, va="top", ha="left")
fig.legend(handles=[Rectangle((0, 0), 1, 1, color=AZUL), Rectangle((0, 0), 1, 1, color=LARANJA)],
           labels=["orientação original", "rotacionada 90°"], loc="lower center", ncol=2, frameon=False,
           bbox_to_anchor=(0.5, -0.02), fontsize=13)
fig.tight_layout(rect=(0, 0.02, 1, topo))
a.saida.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(a.saida, dpi=200, bbox_inches="tight", pad_inches=0.25, facecolor="white")
print("gerado", a.saida)
