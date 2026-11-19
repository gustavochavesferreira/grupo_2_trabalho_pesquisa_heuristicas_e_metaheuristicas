"""Gera as figuras da apresentação a partir de um lote de benchmark (seis métodos; o Haleat não é desenhado).

Uso (na raiz do projeto; requer matplotlib, que não é dependência do projeto):
    python3 docs/apresentacao/gerar_figuras.py --lote results/benchmark_estendido_s3_j6/congelada_v2

Saída padrão: docs/apresentacao/img/<nome do lote>/ (mude com --saida).
O lote é um diretório com `execucoes/<instancia>__<metodo>__<semente>/` (CSV de
resultado + .solucao.csv); se houver `resumo.csv` no lote, ele é usado. Exige a
matriz completa: todas as instâncias com os seis métodos e as mesmas sementes.
Instâncias dos desenhos de solução: escolhidas automaticamente ou por
--destaque INSTANCIA e --ilustracao INSTANCIA.
"""
import argparse
import csv
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.patches import FancyBboxPatch, Rectangle

RAIZ = Path(__file__).resolve().parents[2]
_args = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
_args.add_argument("--lote", type=Path, default=RAIZ / "results/benchmark_estendido_s3_j6/congelada_v2")
_args.add_argument("--saida", type=Path, help="padrão: docs/apresentacao/img/<nome do lote>")
_args.add_argument("--destaque", help="instância do desenho da melhor solução (fig4)")
_args.add_argument("--ilustracao", help="instância do desenho ilustrativo (fig5)")
ARGS = _args.parse_args()
DADOS = ARGS.lote.resolve()
_nome_lote = DADOS.parent.name if DADOS.name == "congelada_v2" else DADOS.name
SAIDA = (ARGS.saida or Path(__file__).resolve().parent / "img" / _nome_lote).resolve()
SAIDA.mkdir(parents=True, exist_ok=True)

# Paleta: azul = propostas H, cinza = controle aleatório, laranja = literatura.
AZUL, AZUL_CLARO, LARANJA, CINZA = "#2a78d6", "#a9c8ef", "#eb6834", "#8c8b86"
TEXTO, TEXTO2, GRADE = "#0b0b0b", "#52514e", "#e4e3df"
METODOS_LOTE = ["Hbase", "Hext", "Hint", "Hcomb", "Haleat", "RLS-f7"]  # o lote precisa ter os seis
OCULTOS = {"Haleat"}  # executado, mas fora das figuras
METODOS = [m for m in METODOS_LOTE if m not in OCULTOS]
COR = {m: AZUL for m in METODOS[:4]} | {"RLS-f7": LARANJA}
FAMILIAS = ["A", "BENG", "CLASS"]
MARCOS = [("0_1", 0.1), ("1", 1), ("5", 5), ("10", 10), ("30", 30), ("60", 60)]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 13, "text.color": TEXTO,
    "axes.labelcolor": TEXTO2, "axes.edgecolor": GRADE, "xtick.color": TEXTO2,
    "ytick.color": TEXTO2, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 200,
})

if (DADOS / "resumo.csv").exists():
    linhas = list(csv.DictReader(open(DADOS / "resumo.csv", encoding="utf-8")))
else:
    linhas = [next(csv.DictReader(open(f, encoding="utf-8")))
              for f in sorted(DADOS.glob("execucoes/*/*.csv")) if not f.name.endswith(".solucao.csv")]
assert linhas, f"nenhuma execução em {DADOS}"
assert all(r["validada"] == "1" for r in linhas), "há execução não validada"


def ordem_instancia(nome):
    fam = next(r["familia"] for r in linhas if r["instancia"] == nome)
    num = tuple(int("".join(c for c in parte if c.isdigit()) or 0) for parte in nome.split("_"))
    return (FAMILIAS.index(fam) if fam in FAMILIAS else 99, nome.rstrip("0123456789_") if fam != "CLASS" else "", num)


def rotulo(nome):
    if nome.startswith("cl_"):
        _, classe, tam, rep = nome.split("_")
        return f"CLASS {int(classe)}/{int(tam)}/{rep}"
    return nome


INSTANCIAS = sorted({r["instancia"] for r in linhas}, key=ordem_instancia)
SEMENTES = sorted({int(r["semente"]) for r in linhas})
_matriz = defaultdict(int)
for r in linhas:
    _matriz[(r["instancia"], r["metodo"], int(r["semente"]))] += 1
_faltam = [(i, m, s) for i in INSTANCIAS for m in METODOS_LOTE for s in SEMENTES if _matriz[(i, m, s)] != 1]
assert not _faltam and len(linhas) == len(INSTANCIAS) * len(METODOS_LOTE) * len(SEMENTES), \
    f"matriz incompleta ou duplicada em {DADOS}: {_faltam[:5]}"
print(f"lote: {DADOS} ({len(INSTANCIAS)} instâncias × {len(METODOS_LOTE)} métodos × {len(SEMENTES)} sementes"
      f" = {len(linhas)} execuções; figuras sem {', '.join(sorted(OCULTOS))})")
linhas = [r for r in linhas if r["metodo"] not in OCULTOS]
por_metodo = defaultdict(list)
for r in linhas:
    por_metodo[r["metodo"]].append(r)


def salva(fig, nome):
    fig.savefig(SAIDA / nome, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("gerado", SAIDA / nome)


def titulo(ax, texto, sub):
    ax.set_title(texto, loc="left", fontsize=17, fontweight="bold", pad=30)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=12, color=TEXTO2)


# 1. Desvio para LBref por execução (dot plot) -------------------------------
fig, ax = plt.subplots(figsize=(11, 5.2))
for y, m in enumerate(reversed(METODOS)):
    desvios = sorted(float(r["desvio"]) for r in por_metodo[m])
    total = defaultdict(int)
    for d in desvios:
        total[round(d, 2)] += 1
    contagem = defaultdict(int)
    for d in desvios:  # espalha valores repetidos verticalmente, dentro de ±0,3
        n, k = total[round(d, 2)], contagem[round(d, 2)]
        contagem[round(d, 2)] += 1
        off = (k - (n - 1) / 2) * min(0.07, 0.6 / max(n - 1, 1))
        ax.scatter(d, y + off, s=55, color=COR[m], alpha=0.55, edgecolor="white", linewidth=1.5, zorder=3)
    media = st.mean(desvios)
    ax.plot([media, media], [y - 0.33, y + 0.33], color=TEXTO, linewidth=2.5, zorder=4)
    ax.text(media, y + 0.38, f"média {media:.1f}%".replace(".", ","), ha="center", va="bottom", fontsize=11, color=TEXTO)
ax.set_yticks(range(len(METODOS)), list(reversed(METODOS)))
ax.set_ylim(-0.6, len(METODOS) - 0.2)
ax.set_xlabel("Desvio de K para LBref (%)  —  menor é melhor")
ax.grid(axis="x", color=GRADE, linewidth=0.8)
ax.set_axisbelow(True)
titulo(ax, "Qualidade das soluções por método",
       f"Cada ponto é uma execução ({len(INSTANCIAS)} instâncias × {len(SEMENTES)} sementes, "
       "60 s de CPU). Traço = média.")
salva(fig, "fig1_desvio_por_metodo.png")

# 2. Evolução do desvio ao longo do tempo ------------------------------------
fig, ax = plt.subplots(figsize=(11, 5.2))
series = {
    "Propostas H (média das 4)": ([r for m in METODOS[:4] for r in por_metodo[m]], AZUL, "-", 4),
    "RLS-f7 (literatura)": (por_metodo["RLS-f7"], LARANJA, "-", 4),
}
xs = [t for _, t in MARCOS]
curvas = {nome: [st.mean(float(r[f"desvio_{s}"]) for r in rs) for s, _ in MARCOS]
          for nome, (rs, *_) in series.items()}
topo = max(5, math.ceil(max(max(v) for v in curvas.values()) * 1.1 / 5) * 5)
for nome, (rs, cor, estilo, z) in series.items():
    ax.plot(xs, curvas[nome], color=cor, linewidth=2.5, linestyle=estilo, marker="o", markersize=8,
            markeredgecolor="white", markeredgewidth=2, zorder=z)
# Rótulos diretos no fim das linhas, afastados para não se sobreporem.
fim = sorted(curvas, key=lambda n: curvas[n][-1])
pos, folga = [], topo * 0.07
for nome in fim:
    y = curvas[nome][-1]
    pos.append(max(y, pos[-1] + folga) if pos else y)
desloc = (pos[0] + pos[-1]) / 2 - (curvas[fim[0]][-1] + curvas[fim[-1]][-1]) / 2
for nome, y in zip(fim, pos):
    ax.text(68, max(y - desloc, topo * 0.03), f"{nome}  {curvas[nome][-1]:.1f}%".replace(".", ","),
            va="center", fontsize=12, color=TEXTO)
ax.set_xscale("log")
ax.set_xticks([t for _, t in MARCOS], ["0,1 s", "1 s", "5 s", "10 s", "30 s", "60 s"])
ax.minorticks_off()
ax.set_ylim(0, topo)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
ax.set_ylabel("Desvio médio para LBref (%)")
ax.set_xlabel("Tempo de CPU (escala log)")
ax.grid(axis="y", color=GRADE, linewidth=0.8)
ax.set_axisbelow(True)
titulo(ax, "Evolução da qualidade ao longo do tempo",
       "Melhor K encontrado até cada instante, média das execuções.")
salva(fig, "fig2_evolucao_tempo.png")

# 3. Heatmap: K por instância × método, cor = chapas a mais que o melhor método --
fig, ax = plt.subplots(figsize=(11, 1.6 + 0.5 * len(INSTANCIAS)))
seq = matplotlib.colors.LinearSegmentedColormap.from_list("azul", ["#f7f9fc", "#a9c8ef", "#2a78d6", "#123f78"])
matriz, textos, otimos = [], [], []
for i in INSTANCIAS:
    medias, txt = [], []
    lb = int(next(r["LBref"] for r in linhas if r["instancia"] == i))
    for m in METODOS:
        rs = sorted((r for r in por_metodo[m] if r["instancia"] == i), key=lambda r: int(r["semente"]))
        ks = [int(r["K"]) for r in rs]
        medias.append(st.mean(ks))
        txt.append("/".join(map(str, ks)))
    matriz.append([v - min(medias) for v in medias])
    textos.append(txt)
    otimos.append([v == lb for v in medias])
vmax = max(1.0, max(max(l) for l in matriz))
im = ax.imshow(matriz, cmap=seq, vmin=0, vmax=vmax, aspect="auto")
for a in range(len(INSTANCIAS)):
    for b in range(len(METODOS)):
        ax.text(b, a, textos[a][b], ha="center", va="center", fontsize=11,
                fontweight="bold" if otimos[a][b] else "normal",
                color="white" if matriz[a][b] >= vmax / 2 else TEXTO)
lbs = {r["instancia"]: r["LBref"] for r in linhas}
ax.set_yticks(range(len(INSTANCIAS)), [f"{rotulo(i)}  (LB={lbs[i]})" for i in INSTANCIAS])
ax.set_xticks(range(len(METODOS)), METODOS)
ax.xaxis.tick_top()
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xticks([x - 0.5 for x in range(1, len(METODOS))], minor=True)
ax.set_yticks([y - 0.5 for y in range(1, len(INSTANCIAS))], minor=True)
ax.grid(which="minor", color="white", linewidth=3)
ax.tick_params(which="minor", length=0)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cb.set_label("Chapas a mais que o melhor método (média)", color=TEXTO2)
cb.outline.set_visible(False)
ax.set_title(f"K obtido em cada semente ({'/'.join(map(str, SEMENTES))})", loc="left", fontsize=17,
             fontweight="bold", pad=48)
ax.annotate("Negrito: atingiu LBref em todas as sementes (ótimo comprovado).", xy=(0, 1), xycoords="axes fraction",
            xytext=(0, 30), textcoords="offset points", fontsize=11, color=TEXTO2, va="bottom", ha="left")
salva(fig, "fig3_k_por_instancia.png")

# 4. Desenho de uma solução --------------------------------------------------
def pct(parte, total):
    """Percentual com 1 casa e vírgula; só mostra 100% se a área estiver de fato cheia."""
    if parte == total:
        return "100%"
    return f"{int(1000 * parte / total) / 10:.1f}%".replace(".", ",")


def desenha_solucao(instancia, metodo, semente, nome, colunas=None):
    if metodo is None:  # melhor K da instância (empate: ordem de METODOS e semente)
        melhor = min((r for r in linhas if r["instancia"] == instancia),
                     key=lambda r: (int(r["K"]), METODOS.index(r["metodo"]), int(r["semente"])))
        metodo, semente = melhor["metodo"], int(melhor["semente"])
    pasta = DADOS / "execucoes" / f"{instancia}__{metodo}__{semente}"
    arquivo = next(pasta.glob("*.solucao.csv"))
    pecas = list(csv.DictReader(open(arquivo, encoding="utf-8")))
    caminho = next(r["caminho_instancia"] for r in linhas
                   if r["instancia"] == instancia and r["metodo"] == metodo and r["semente"] == str(semente))
    W, H = map(int, open(caminho).read().split()[1:3])
    lb = next(r["LBref"] for r in linhas if r["instancia"] == instancia)
    chapas = sorted({int(p["chapa"]) for p in pecas})
    colunas = colunas or min(5, max(3, math.ceil(math.sqrt(len(chapas) * 1.5))))
    lin = (len(chapas) + colunas - 1) // colunas
    fig, eixos = plt.subplots(lin, colunas, figsize=(3.0 * colunas, 3.0 * lin * H / W + 0.6 * lin))
    eixos = eixos.ravel()
    for ax in eixos:
        ax.axis("off")
    area_total = 0
    for c in chapas:
        ax = eixos[c]
        ax.add_patch(Rectangle((0, 0), W, H, facecolor="#f4f3ef", edgecolor=TEXTO2, linewidth=1.2))
        area = 0
        for p in (p for p in pecas if int(p["chapa"]) == c):
            x, y, w, h = (int(p[k]) for k in ("x", "y", "largura", "altura"))
            area += w * h
            cor = LARANJA if p["rotacionada"] == "1" else AZUL
            ax.add_patch(Rectangle((x, y), w, h, facecolor=cor, edgecolor="white", linewidth=1.5, alpha=0.85))
        area_total += area
        ax.set_xlim(-W * 0.02, W * 1.02)
        ax.set_ylim(-H * 0.02, H * 1.02)
        ax.set_aspect("equal")
        ax.set_title(f"Chapa {c + 1} — {pct(area, W * H)} ocupada", fontsize=11, color=TEXTO2)
    fig.suptitle(f"{rotulo(instancia)} · {metodo} · K = {len(chapas)} (LBref = {lb}) · "
                 f"ocupação média {pct(area_total, W * H * len(chapas))}",
                 fontsize=15, fontweight="bold", x=0.02, ha="left")
    fig.legend(handles=[Rectangle((0, 0), 1, 1, color=AZUL), Rectangle((0, 0), 1, 1, color=LARANJA)],
               labels=["orientação original", "rotacionada 90°"], loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout()
    salva(fig, nome)


def ks_da(instancia):
    return [int(r["K"]) for r in linhas if r["instancia"] == instancia]


def lb_da(instancia):
    return int(next(r["LBref"] for r in linhas if r["instancia"] == instancia))


# fig4: instância em que só parte das execuções chega ao melhor K (de preferência o ótimo).
destaque = ARGS.destaque
if destaque is None:
    candidatas = [i for i in INSTANCIAS if min(ks_da(i)) < max(ks_da(i)) and min(ks_da(i)) <= 30]
    destaque = min(candidatas, key=lambda i: (min(ks_da(i)) != lb_da(i), min(ks_da(i))), default=None)
if destaque:
    desenha_solucao(destaque, None, None, f"fig4_solucao_{destaque}.png")

# fig5: ilustração do problema — ótimo atingido por todos, a com mais peças entre 5 e 12 chapas.
ilustracao = ARGS.ilustracao
if ilustracao is None:
    def n_pecas(i):
        r = next(r for r in linhas if r["instancia"] == i)
        pasta = DADOS / "execucoes" / f"{i}__{r['metodo']}__{r['semente']}"
        return sum(1 for _ in open(next(pasta.glob("*.solucao.csv")))) - 1
    candidatas = [i for i in INSTANCIAS if set(ks_da(i)) == {lb_da(i)} and 5 <= lb_da(i) <= 12]
    ilustracao = "BENG03" if "BENG03" in INSTANCIAS else max(candidatas, key=n_pecas, default=None)
if ilustracao:
    desenha_solucao(ilustracao, "Hcomb", SEMENTES[0], f"fig5_solucao_{ilustracao}.png")

# 6. Fluxo da arquitetura proposta ------------------------------------------
fig, ax = plt.subplots(figsize=(13, 3.6))
ax.axis("off")
ax.set_xlim(0, 13)
ax.set_ylim(0.9, 4.6)
caixas = [
    (0.2, "Construção\ninicial", "solução viável\ncom K chapas"),
    (2.75, "Remove a chapa\nmenos ocupada", "redistribui as peças\n(K−1 chapas, inviável)"),
    (5.3, "Reparo por VND", "3 vizinhanças de\nmovimento de peças"),
    (7.85, "Perturbação +\nreinício", "2 chapas perturbadas\naté 50 000 reinícios"),
    (10.4, "Viável?", "sim → nova solução\ncom K−1; repete"),
]
for x, t, s in caixas:
    ax.add_patch(FancyBboxPatch((x, 2.0), 2.3, 1.5, boxstyle="round,pad=0.02,rounding_size=0.12",
                                facecolor="#eaf1fb", edgecolor=AZUL, linewidth=1.8))
    ax.text(x + 1.15, 3.05, t, ha="center", va="center", fontsize=13, fontweight="bold")
    ax.text(x + 1.15, 2.45, s, ha="center", va="center", fontsize=10.5, color=TEXTO2)
for x, _, _ in caixas[:-1]:
    ax.annotate("", xy=(x + 2.55, 2.75), xytext=(x + 2.3, 2.75),
                arrowprops=dict(arrowstyle="-|>", color=TEXTO2, lw=1.8))
ax.annotate("", xy=(9.0, 3.5), xytext=(6.45, 3.5),
            arrowprops=dict(arrowstyle="<|-", color=TEXTO2, lw=1.5, connectionstyle="arc3,rad=-0.35"))
ax.text(7.7, 4.25, "ainda inviável", ha="center", fontsize=11, color=TEXTO2)
ax.text(0.2, 1.2, "Hext: orientação externa (histórico de rejeições guia quais peças mover)    "
        "Hint: busca interna na sequência de cada chapa    Hcomb: ambas",
        fontsize=10.5, color=TEXTO2)
salva(fig, "fig6_fluxo_metodo.png")

# 7–9. Solução inicial × busca (só a arquitetura H) ----------------------------
# K inicial = K final + reduções aceitas (cada redução aceita remove exatamente uma chapa);
# tempo_melhor = instante da última redução aceita (ou do fim da construção, se nenhuma).
METODOS_H = ["Hbase", "Hext", "Hint", "Hcomb"]
CATEGORIAS = [
    ("ini_otima", "Inicial já ótima", "#123f78", "white"),
    ("otimo_busca", "Ótimo alcançado pela busca", AZUL, "white"),
    ("melhorou", "Melhorou, sem provar ótimo", "#a9c8ef", TEXTO),
    ("sem_melhora", "Não melhorou a inicial", "#dedcd6", TEXTO),
]


def k_inicial(r):
    return int(r["K"]) + int(r["reducoes_aceitas"])


def categoria(r):
    k, lb, red = int(r["K"]), int(r["LBref"]), int(r["reducoes_aceitas"])
    if k == lb:
        return "ini_otima" if red == 0 else "otimo_busca"
    return "melhorou" if red > 0 else "sem_melhora"


# fig7: barras empilhadas com o desfecho de cada execução.
fig, ax = plt.subplots(figsize=(11, 4.6))
n_exec = len(INSTANCIAS) * len(SEMENTES)
for y, m in enumerate(reversed(METODOS_H)):
    rs = por_metodo[m]
    esquerda = 0
    for chave, nome, cor, cor_txt in CATEGORIAS:
        n = sum(categoria(r) == chave for r in rs)
        if n == 0:
            continue
        ax.barh(y, n, left=esquerda, height=0.62, color=cor, edgecolor="white", linewidth=2)
        ax.text(esquerda + n / 2, y, str(n), ha="center", va="center", fontsize=12, color=cor_txt,
                fontweight="bold")
        esquerda += n
ax.set_yticks(range(len(METODOS_H)), list(reversed(METODOS_H)))
ax.set_xlim(0, n_exec)
ax.set_xlabel(f"Execuções ({len(INSTANCIAS)} instâncias × {len(SEMENTES)} sementes)")
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
ax.legend(handles=[Rectangle((0, 0), 1, 1, color=c) for _, _, c, _ in CATEGORIAS],
          labels=[n for _, n, _, _ in CATEGORIAS], loc="upper center", bbox_to_anchor=(0.5, -0.2),
          ncol=4, frameon=False, fontsize=11.5, handlelength=1.2)
n_ini = len({r["instancia"] for r in linhas if r["metodo"] in METODOS_H and categoria(r) == "ini_otima"})
titulo(ax, "A solução inicial já é ótima? E a busca, o que acrescenta?",
       f"A construção inicial é determinística: já é ótima em {n_ini} das {len(INSTANCIAS)} instâncias, "
       "para todos os métodos.")
salva(fig, "fig7_inicial_vs_busca.png")

# fig8: tempo até a solução final, só nas execuções em que a busca melhorou a inicial.
fig, ax = plt.subplots(figsize=(11, 4.8))
cores_cat = {c: cor for c, _, cor, _ in CATEGORIAS}
for y, m in enumerate(reversed(METODOS_H)):
    rs = [r for r in por_metodo[m] if categoria(r) in ("otimo_busca", "melhorou")]
    tempos = sorted((max(float(r["tempo_melhor"]), 1e-3), categoria(r)) for r in rs)
    for k, (t, cat) in enumerate(tempos):
        off = ((k % 3) - 1) * 0.12
        ax.scatter(t, y + off, s=60, color=cores_cat[cat], edgecolor="white" if cat == "otimo_busca" else AZUL,
                   linewidth=1.2, zorder=3)
    if tempos:
        med = st.median(t for t, _ in tempos)
        ax.plot([med, med], [y - 0.32, y + 0.32], color=TEXTO, linewidth=2.5, zorder=4)
        ax.text(med, y + 0.36, f"mediana {med:.2g} s".replace(".", ","), ha="center", va="bottom", fontsize=10.5)
ax.set_xscale("log")
ax.set_xlim(1e-3 * 0.7, 60 * 1.4)
ax.set_xticks([1e-3, 1e-2, 0.1, 1, 10, 60], ["≤1 ms", "10 ms", "0,1 s", "1 s", "10 s", "60 s"])
ax.minorticks_off()
ax.set_yticks(range(len(METODOS_H)), list(reversed(METODOS_H)))
ax.set_ylim(-0.6, len(METODOS_H) - 0.2)
ax.set_xlabel("Tempo de CPU até a solução final (escala log)")
ax.grid(axis="x", color=GRADE, linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", ms=9, mfc=cores_cat[c], mec="white" if c == "otimo_busca" else AZUL)
                   for c in ("otimo_busca", "melhorou")],
          labels=["chegou ao ótimo", "melhorou, sem provar ótimo"], loc="upper center",
          bbox_to_anchor=(0.5, -0.17), ncol=2, frameon=False, fontsize=11.5)
titulo(ax, "Quando a inicial não é ótima: quanto tempo até a solução final?",
       "Só execuções em que a busca reduziu chapas. Ponto = instante da última redução. Traço = mediana.")
salva(fig, "fig8_tempo_ate_solucao.png")

# fig9: por instância, K inicial → melhor e pior K final das propostas H, em chapas acima de LBref.
inst_nao_otimas = [i for i in INSTANCIAS
                   if k_inicial(next(r for r in linhas if r["instancia"] == i and r["metodo"] == "Hbase")) > lb_da(i)]
if inst_nao_otimas:
    fig, ax = plt.subplots(figsize=(11, 1.6 + 0.45 * len(inst_nao_otimas)))
    for y, i in enumerate(reversed(inst_nao_otimas)):
        rs = [r for r in linhas if r["instancia"] == i and r["metodo"] in METODOS_H[:4]]
        lb, ki = lb_da(i), k_inicial(rs[0])
        kmin, kmax = min(int(r["K"]) for r in rs), max(int(r["K"]) for r in rs)
        ax.annotate("", xy=(kmax - lb, y), xytext=(ki - lb, y),
                    arrowprops=dict(arrowstyle="-|>", color=AZUL_CLARO, lw=2.2, shrinkA=6, shrinkB=6))
        if kmin < kmax:
            ax.plot([kmin - lb, kmax - lb], [y, y], color=AZUL, lw=5, solid_capstyle="round", zorder=3)
        ax.scatter(ki - lb, y, s=90, color="white", edgecolor=CINZA, linewidth=2, zorder=4)
        ax.scatter([kmin - lb], [y], s=90, color=AZUL, edgecolor="white", linewidth=1.5, zorder=5)
        ax.text(ki - lb + 0.25, y, f"{ki} → {kmin}" + (f"–{kmax}" if kmin < kmax else ""),
                va="center", fontsize=10.5, color=TEXTO2)
    ax.axvline(0, color=TEXTO, lw=1.2)
    ax.set_yticks(range(len(inst_nao_otimas)),
                  [f"{rotulo(i)}  (LB={lb_da(i)})" for i in reversed(inst_nao_otimas)])
    ax.set_xlabel("Chapas acima de LBref  (0 = ótimo comprovado)")
    ax.set_xlim(-0.4, max(k_inicial(r) - int(r["LBref"]) for r in linhas if r["metodo"] in METODOS_H) + 1.8)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.grid(axis="x", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", ms=9, mfc="white", mec=CINZA, mew=2),
                       plt.Line2D([], [], marker="o", ls="", ms=9, mfc=AZUL, mec="white"),
                       plt.Line2D([], [], color=AZUL, lw=5)],
              labels=["solução inicial", "melhor K final", "faixa entre execuções"], loc="upper center",
              bbox_to_anchor=(0.5, -0.9 / len(inst_nao_otimas) - 0.08), ncol=3, frameon=False, fontsize=11.5)
    titulo(ax, "Da solução inicial à final, por instância",
           f"Instâncias em que a inicial não é ótima ({len(inst_nao_otimas)} de {len(INSTANCIAS)}). "
           "Hbase, Hext, Hint e Hcomb, todas as sementes.")
    salva(fig, "fig9_inicial_para_final.png")
