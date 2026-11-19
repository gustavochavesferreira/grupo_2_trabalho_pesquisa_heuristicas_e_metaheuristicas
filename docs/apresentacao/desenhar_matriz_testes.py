"""Diagrama da matriz de testes (catálogo → piloto/final → benchmark completo).

Uso (na raiz do projeto; requer matplotlib):
    python3 docs/apresentacao/desenhar_matriz_testes.py [--saida docs/apresentacao/img/matriz_testes.png]

As contagens vêm de instances/manifests/*.csv; métodos e sementes são os do benchmark completo.
"""
import argparse
import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

RAIZ = Path(__file__).resolve().parents[2]
_a = argparse.ArgumentParser(description=__doc__)
_a.add_argument("--inicial", choices=["aleatoria", "gulosa"], default="aleatoria")
_a.add_argument("--saida", type=Path, help="padrão: img/matriz_testes.png (aleatória) ou img/matriz_testes_gulosa.png")
_args = _a.parse_args()
INICIAL = _args.inicial
SAIDA = _args.saida or Path(__file__).resolve().parent / "img" / (
    "matriz_testes.png" if INICIAL == "aleatoria" else "matriz_testes_gulosa.png")

AZUL, AZUL_CLARO, LARANJA, CINZA = "#2a78d6", "#e3eefb", "#eb6834", "#8c8b86"
TEXTO, TEXTO2, GRADE, FUNDO = "#0b0b0b", "#52514e", "#e4e3df", "#f4f3ef"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXTO})


def le(nome):
    return list(csv.DictReader(open(RAIZ / "instances/manifests" / nome, encoding="utf-8")))


cat, pil, fin = le("catalogo.csv"), le("piloto.csv"), le("final.csv")
n = lambda linhas, f: sum(r["familia"] == f for r in linhas)  # noqa: E731
FAM = ["A", "BENG", "CLASS"]
assert len(fin) == 153 and len(pil) == 10, "manifests diferentes dos usados no benchmark completo"
classe_fin = Counter(r["classe"] for r in fin if r["familia"] == "CLASS")
METODOS = [("Hbase", AZUL), ("Hext", AZUL), ("Hint", AZUL), ("Hcomb", AZUL), ("RLS-f7", LARANJA)]
SEMENTES = 10

fig, ax = plt.subplots(figsize=(16, 9.6))
ax.set_xlim(0, 16)
ax.set_ylim(0, 9.6)
ax.axis("off")


def caixa(x, y, w, h, cor_borda=GRADE, fundo="white", lw=1.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                facecolor=fundo, edgecolor=cor_borda, linewidth=lw))


def seta(x0, y0, x1, y1, texto=None, cor=TEXTO2):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=18,
                                 color=cor, linewidth=1.8, shrinkA=0, shrinkB=0))
    if texto:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.12, texto, ha="center", va="bottom", fontsize=10, color=TEXTO2)


def bloco(x, y, w, h, titulo, linhas, borda=GRADE, fundo="white", tam=11.5):
    caixa(x, y, w, h, borda, fundo)
    ax.text(x + 0.2, y + h - 0.2, titulo, fontsize=13.5, fontweight="bold", va="top")
    for i, l in enumerate(linhas):
        ax.text(x + 0.2, y + h - 0.68 - 0.36 * i, l, fontsize=tam, color=TEXTO2, va="top")


ax.text(0.05, 9.45, "Matriz de testes", fontsize=19, fontweight="bold", va="top")
ax.text(0.05, 8.98, "Do catálogo de instâncias ao benchmark completo. "
        "Cada execução: 1 instância × 1 método × 1 semente, até 60 s de CPU.", fontsize=12, color=TEXTO2, va="top")

# Linha de cima: catálogo → piloto (escolhe H*) e conjunto final ---------------------
bloco(0.05, 5.55, 3.4, 2.85, "Catálogo",
      [f"{len(cat)} instâncias", f"• A: {n(cat, 'A')}", f"• BENG: {n(cat, 'BENG')}", f"• CLASS: {n(cat, 'CLASS')}",
       "(10 classes × 5 tamanhos", "  × 10 réplicas)"])
bloco(4.4, 6.75, 5.3, 1.95, "Piloto: escolhe H*",
      [f"{len(pil)} instâncias ({n(pil, 'A')} A + {n(pil, 'CLASS')} CLASS) × 4 propostas H",
       f"× {SEMENTES} sementes = {len(pil) * 4 * SEMENTES} execuções",
       "Critério: menor desvio médio → H* = Hbase"], borda=GRADE, fundo=FUNDO)
bloco(4.4, 4.1, 5.3, 2.3, f"Conjunto final: {len(fin)} instâncias",
      [f"• A: {n(fin, 'A')} (todas, menos as 5 do piloto)", f"• BENG: {n(fin, 'BENG')} (todas)",
       f"• CLASS: {n(fin, 'CLASS')} = 10 classes × 5 tamanhos",
       "   × 2 réplicas, + 5 extras"],
      borda=AZUL, fundo=AZUL_CLARO)
seta(3.45, 7.6, 4.4, 7.6)
seta(3.45, 6.1, 4.4, 5.3)
seta(7.05, 6.75, 7.05, 6.4, None)
ax.text(7.2, 6.57, "H* vai para os testes pareados", fontsize=9.5, color=TEXTO2, va="center")

# Direita: o que cada execução recebe -------------------------------------------------
bloco(10.6, 4.1, 5.3, 4.6, "Cada execução",
      [f"• Instância e método ({len(METODOS)} opções)",
       *([f"• Sementes 1001 a {1000 + SEMENTES}: mesma",
          "  semente = mesma solução inicial",
          "  aleatória em todos os métodos",
          "  (partida igual à da RLS-f7)"] if INICIAL == "aleatoria" else
         [f"• Sementes 1001 a {1000 + SEMENTES}; todos",
          "  partem da construção gulosa",
          "  (RLS-f7 em variante diagnóstica",
          "  com inicial gulosa)"]),
       "• Limite: 60 s de CPU, ou para ao",
       "  atingir LBref",
       "• 6 processos, cada um fixo num",
       "  núcleo físico; ordem sorteada",
       "• Toda solução é validada"])
seta(9.7, 5.25, 10.6, 5.25)

# Embaixo: a matriz instâncias × métodos ------------------------------------------------
x0, y0, wl, wc, hl = 0.05, 0.25, 2.6, 1.82, 0.62
ax.text(x0, 3.75, f"Benchmark completo: {len(fin)} instâncias × {len(METODOS)} métodos × {SEMENTES} sementes",
        fontsize=14, fontweight="bold", va="top")
grupos = [("Propostas H", 0, 4, AZUL), ("Literatura", 4, 5, LARANJA)]
for nome, a, b, cor in grupos:
    xa, xb = x0 + wl + a * wc + 0.08, x0 + wl + b * wc - 0.08
    ax.plot([xa, xb], [3.2, 3.2], color=cor, linewidth=2.5, solid_capstyle="round")
    ax.text((xa + xb) / 2, 3.26, nome, ha="center", va="bottom", fontsize=10.5, color=TEXTO2)
ytopo = y0 + hl * 4
for j, (m, cor) in enumerate(METODOS):
    ax.text(x0 + wl + (j + 0.5) * wc, ytopo + 0.2, m, ha="center", va="center", fontsize=12.5,
            fontweight="bold", color=cor)
for i, f in enumerate(FAM):
    y = ytopo - (i + 1) * hl
    ni = n(fin, f)
    ax.text(x0 + 0.1, y + hl / 2, f"{f}  ({ni} inst.)", va="center", fontsize=12.5, fontweight="bold")
    for j, (m, cor) in enumerate(METODOS):
        x = x0 + wl + j * wc
        caixa(x + 0.04, y + 0.04, wc - 0.08, hl - 0.08, GRADE, FUNDO, 1)
        ax.text(x + wc / 2, y + hl / 2, f"{ni} × {SEMENTES} = {ni * SEMENTES}", ha="center", va="center",
                fontsize=10, color=TEXTO)
    xt = x0 + wl + len(METODOS) * wc
    ax.text(xt + 0.2, y + hl / 2, f"{ni * SEMENTES * len(METODOS)}", va="center", fontsize=12.5, fontweight="bold")
ax.text(x0 + wl + len(METODOS) * wc + 0.2, ytopo + 0.2, "Total", va="center", fontsize=12.5, color=TEXTO2)
yt = ytopo - 4 * hl
ax.plot([x0, x0 + wl + len(METODOS) * wc + 1.3], [yt + hl - 0.02] * 2, color=TEXTO2, linewidth=1)
for j in range(len(METODOS)):
    ax.text(x0 + wl + (j + 0.5) * wc, yt + hl / 2, f"{len(fin) * SEMENTES}", ha="center", va="center",
            fontsize=12, fontweight="bold")
ax.text(x0 + 0.1, yt + hl / 2, "Total", va="center", fontsize=12.5, color=TEXTO2)
ax.text(x0 + wl + len(METODOS) * wc + 0.2, yt + hl / 2, f"{len(fin) * SEMENTES * len(METODOS)}",
        va="center", fontsize=14, fontweight="bold", color=AZUL)
ax.text(15.95, 0.12, "CLASS no final: " + ", ".join(f"{int(c):02d}: {classe_fin[c]}" for c in sorted(classe_fin, key=int)),
        ha="right", va="bottom", fontsize=9.5, color=TEXTO2)

SAIDA.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(SAIDA, dpi=200, bbox_inches="tight", pad_inches=0.25, facecolor="white")
print("gerado", SAIDA)
