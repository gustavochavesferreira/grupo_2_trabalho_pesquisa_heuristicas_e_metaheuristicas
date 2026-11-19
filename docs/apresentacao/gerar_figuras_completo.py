"""Figuras do benchmark completo, segmentadas por dataset (A, BENG e as 10 classes de CLASS).

Uso (na raiz do projeto; requer matplotlib, que não é dependência do projeto):
    python3 docs/apresentacao/gerar_figuras_completo.py \
        [--lote results/benchmark_completo_paralelo_j6/aleatoria/congelada_v2] [--saida DIR]

Saída padrão: docs/apresentacao/img/benchmark_completo_<inicial>/.
Exige a matriz completa (instâncias × seis métodos × mesmas sementes), toda validada.
"""
import argparse
import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

RAIZ = Path(__file__).resolve().parents[2]
_a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
_a.add_argument("--lote", type=Path, default=RAIZ / "results/benchmark_completo_paralelo_j6/aleatoria/congelada_v2")
_a.add_argument("--saida", type=Path)
ARGS = _a.parse_args()
DADOS = ARGS.lote.resolve()
INICIAL = DADOS.parent.name
ROTULO_INICIAL = {"aleatoria": "aleatória", "gulosa": "gulosa"}.get(INICIAL, INICIAL)
# Com inicial gulosa, a RLS-f7 roda numa variante diagnóstica (--inicial gulosa), não na versão publicada.
NOTA_RLS = " RLS-f7 na variante com inicial gulosa (não é a publicada)." if INICIAL == "gulosa" else ""
SAIDA = (ARGS.saida or Path(__file__).resolve().parent / "img" / f"benchmark_completo_{INICIAL}").resolve()
SAIDA.mkdir(parents=True, exist_ok=True)

AZUL, LARANJA, CINZA = "#2a78d6", "#eb6834", "#8c8b86"
TEXTO, TEXTO2, GRADE, FUNDO = "#0b0b0b", "#52514e", "#e4e3df", "#f4f3ef"
METODOS_LOTE = ["Hbase", "Hext", "Hint", "Hcomb", "Haleat", "RLS-f7"]  # o lote precisa ter os seis
OCULTOS = {"Haleat"}  # executado, mas fora das figuras
METODOS = [m for m in METODOS_LOTE if m not in OCULTOS]
MARCOS = [("0_1", 0.1), ("1", 1), ("5", 5), ("10", 10), ("30", 30), ("60", 60)]
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 13, "text.color": TEXTO,
    "axes.labelcolor": TEXTO2, "axes.edgecolor": GRADE, "xtick.color": TEXTO2,
    "ytick.color": TEXTO2, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 200,
})


def virgula(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


linhas = [next(csv.DictReader(open(f, encoding="utf-8")))
          for f in sorted(DADOS.glob("execucoes/*/*.csv")) if not f.name.endswith(".solucao.csv")]
assert linhas and all(r["validada"] == "1" for r in linhas), "lote vazio ou com execução não validada"
INSTANCIAS = sorted({r["instancia"] for r in linhas})
SEMENTES = sorted({r["semente"] for r in linhas})
_cont = defaultdict(int)
for r in linhas:
    _cont[(r["instancia"], r["metodo"], r["semente"])] += 1
assert all(_cont[(i, m, s)] == 1 for i in INSTANCIAS for m in METODOS_LOTE for s in SEMENTES) and \
    len(linhas) == len(INSTANCIAS) * len(METODOS_LOTE) * len(SEMENTES), "matriz incompleta ou duplicada"
print(f"lote: {DADOS} ({len(INSTANCIAS)} instâncias × {len(METODOS_LOTE)} métodos × {len(SEMENTES)} sementes;"
      f" figuras sem {', '.join(sorted(OCULTOS))})")
linhas = [r for r in linhas if r["metodo"] not in OCULTOS]


def grupo(r):
    return r["familia"] if r["familia"] != "CLASS" else f"CLASS {r['instancia'].split('_')[1]}"


GRUPOS = ["A", "BENG"] + [f"CLASS {c:02d}" for c in range(1, 11)]
FAMILIAS = ["A", "BENG", "CLASS"]
por = defaultdict(list)  # (grupo, metodo) -> execuções
for r in linhas:
    por[(grupo(r), r["metodo"])].append(r)
GRUPOS = [g for g in GRUPOS if por[(g, "Hbase")]]
n_inst = {g: len({r["instancia"] for r in por[(g, "Hbase")]}) for g in GRUPOS}


def salva(fig, nome):
    fig.savefig(SAIDA / nome, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("gerado", SAIDA / nome)


def cabecalho(fig, texto, sub):
    fig.text(0.01, 1.0, texto, fontsize=17, fontweight="bold", va="bottom", ha="left")
    fig.text(0.01, 0.985, sub, fontsize=12, color=TEXTO2, va="top", ha="left")


# C1. Tabela de calor: desvio médio e alcance do LBref, por dataset × método --------
def tabela(ax, valores, fmt, menor_melhor, titulo_painel, saturacao):
    """Cor = distância absoluta para o melhor da linha (satura em `saturacao`); melhor em negrito."""
    cmap = LinearSegmentedColormap.from_list("dist", ["#ffffff", "#c9c7c0", "#8c8b86"])
    for y, g in enumerate(GRUPOS):
        linha = valores[g]
        melhor = min(linha) if menor_melhor else max(linha)
        for x, v in enumerate(linha):
            dist = min(1.0, abs(v - melhor) / saturacao)  # float: cmap(1) (int) seria o índice 1
            ax.add_patch(plt.Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor=cmap(dist),
                                       edgecolor="white", linewidth=2))
            ax.text(x, y, fmt(v), ha="center", va="center", fontsize=11.5, color=TEXTO,
                    fontweight="bold" if abs(v - melhor) < 1e-9 else "normal")
    ax.set_xlim(-0.5, len(METODOS) - 0.5)
    ax.set_ylim(len(GRUPOS) - 0.5, -0.5)
    ax.set_xticks(range(len(METODOS)), METODOS, fontsize=11.5)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(titulo_painel, fontsize=13.5, color=TEXTO, pad=34, loc="left")
    for t, m in zip(ax.get_xticklabels(), METODOS):
        t.set_color(LARANJA if m == "RLS-f7" else AZUL)


desvio = {g: [st.mean(float(r["desvio"]) for r in por[(g, m)]) for m in METODOS] for g in GRUPOS}
alcance = {g: [100 * st.mean(int(r["alcancou_lb"]) for r in por[(g, m)]) for m in METODOS] for g in GRUPOS}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 7.6), gridspec_kw={"wspace": 0.08})
tabela(a1, desvio, lambda v: virgula(v) + "%", True, "Desvio médio para LBref (menor é melhor)", 1.5)
tabela(a2, alcance, lambda v: f"{v:.0f}%", False, "Execuções que atingem LBref (maior é melhor)", 10)
a1.set_yticks(range(len(GRUPOS)), [f"{g}  ({n_inst[g]})" for g in GRUPOS], fontsize=12)
a2.set_yticks([])
cabecalho(fig, "Resultados por dataset",
          f"{len(INSTANCIAS)} instâncias × {len(SEMENTES)} sementes, 60 s de CPU, inicial {ROTULO_INICIAL}. "
          "Entre parênteses: nº de instâncias.\nNegrito = melhor da linha; cinza = pior que ele "
          "(escuro a partir de 1,5 p.p. / 10 p.p.)." + NOTA_RLS)
fig.subplots_adjust(top=0.81)
salva(fig, "figC1_resumo_por_dataset.png")

# C2. Evolução do desvio no tempo, um painel por família -------------------------
fig, eixos = plt.subplots(1, 3, figsize=(16, 5.4), gridspec_kw={"wspace": 0.28})
omitidos = []
xs = [t for _, t in MARCOS]
for ax, F in zip(eixos, FAMILIAS):
    rs = [r for r in linhas if r["familia"] == F]
    series = [("H (média das 4)", [r for r in rs if r["metodo"] in METODOS[:4]], AZUL, "-", 4),
              ("RLS-f7", [r for r in rs if r["metodo"] == "RLS-f7"], LARANJA, "-", 4)]
    finais = []
    for nome, sub, cor, estilo, z in series:
        # Marco sem valor em alguma execução (a inicial ainda não estava pronta): o ponto é omitido,
        # para não calcular a média sobre só parte das execuções.
        pts = [(t, st.mean(float(r[f"desvio_{s}"]) for r in sub)) for s, t in MARCOS
               if all(r[f"desvio_{s}"] != "" for r in sub)]
        for s, t in MARCOS:
            falta = sum(r[f"desvio_{s}"] == "" for r in sub)
            if falta:
                omitidos.append(f"{F}/{nome}: {falta} execuções sem valor em {virgula(t, 1 if t < 1 else 0)} s")
        xs_s, ys = zip(*pts)
        ax.plot(xs_s, ys, color=cor, linestyle=estilo, linewidth=2.5, marker="o", markersize=7, zorder=z, label=nome)
        finais.append((ys[-1], cor))
    ax.set_ylim(bottom=0)
    (y1, c1), (y2, c2) = sorted(finais)  # afasta os dois rótulos se estiverem próximos
    folga = 0.06 * ax.get_ylim()[1]
    meio = (y1 + y2) / 2
    p1, p2 = (y1, y2) if y2 - y1 >= folga else (meio - folga / 2, meio + folga / 2)
    for y, p in ((y1, p1), (y2, p2)):
        ax.annotate(virgula(y) + "%", (60, y), xytext=(75, p), textcoords="data", va="center", fontsize=11)
    ax.set_xscale("log")
    ax.set_xticks(xs, ["0,1", "1", "5", "10", "30", "60"])
    ax.set_xlim(0.07, 110)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",") + "%"))
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ni = len({r["instancia"] for r in rs})
    ax.set_title(f"{F}  ({ni} instâncias)", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Tempo de CPU (s, escala log)")
eixos[0].set_ylabel("Desvio médio para LBref")
eixos[0].legend(frameon=False, fontsize=11, loc="lower left")
cabecalho(fig, "Evolução da qualidade no tempo, por dataset",
          f"Inicial {ROTULO_INICIAL}. Cada eixo tem sua escala. Rótulos = valor em 60 s." + NOTA_RLS)
fig.subplots_adjust(top=0.84)
if omitidos:
    fig.text(0.01, -0.04, "Ponto omitido quando a solução inicial ainda não estava pronta em alguma execução ("
             + "; ".join(omitidos) + ").", fontsize=10.5, color=TEXTO2, ha="left", va="top")
salva(fig, "figC2_evolucao_por_dataset.png")

# C3. Hbase × RLS-f7, pareado por (instância, semente) ---------------------------
k = {(r["instancia"], r["metodo"], r["semente"]): int(r["K"]) for r in linhas}
grupo_inst = {r["instancia"]: grupo(r) for r in linhas}
cont = {g: [0, 0, 0] for g in GRUPOS}
for i in INSTANCIAS:
    for s in SEMENTES:
        d = k[(i, "Hbase", s)] - k[(i, "RLS-f7", s)]
        cont[grupo_inst[i]][0 if d < 0 else 1 if d == 0 else 2] += 1
fig, ax = plt.subplots(figsize=(13, 6.4))
cores = [AZUL, "#dcdad4", LARANJA]
for y, g in enumerate(GRUPOS):
    tot = sum(cont[g])
    esq = 0
    for j, (c, cor) in enumerate(zip(cont[g], cores)):
        w = 100 * c / tot
        if w:
            ax.barh(y, w, left=esq, height=0.72, color=cor, edgecolor="white", linewidth=2)
            if w >= 6:
                ax.text(esq + w / 2, y, str(c), ha="center", va="center", fontsize=11,
                        color="white" if j != 1 else TEXTO)
        esq += w
    ax.text(101.5, y, f"{cont[g][0]} · {cont[g][1]} · {cont[g][2]}", va="center", fontsize=11, color=TEXTO2)
ax.text(101.5, -0.75, "H · = · RLS", va="center", fontsize=10, color=TEXTO2)
ax.set_yticks(range(len(GRUPOS)), [f"{g}  ({sum(cont[g])})" for g in GRUPOS])
ax.set_ylim(len(GRUPOS) - 0.5, -0.5)
ax.set_xlim(0, 100)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",") + "%"))
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in cores],
          labels=["Hbase usa menos chapas", "empate", "RLS-f7 usa menos chapas"],
          ncol=3, frameon=False, loc="upper left", bbox_to_anchor=(0, 1.1), fontsize=12)
cabecalho(fig, "Hbase (H*) contra RLS-f7, execução a execução",
          f"Mesma instância e mesma semente (mesma solução inicial {ROTULO_INICIAL}); compara o K final. "
          "Entre parênteses: nº de pares." + NOTA_RLS)
fig.subplots_adjust(top=0.84)
salva(fig, "figC3_hbase_vs_rls_por_dataset.png")

# C4. Família A por instância (só onde os métodos diferem) -----------------------
media_k = defaultdict(list)
for r in linhas:
    media_k[(r["instancia"], r["metodo"])].append(float(r["desvio"]))
inst_a = sorted({r["instancia"] for r in linhas if r["familia"] == "A"}, key=lambda s: int(s[1:]))
dif = [i for i in inst_a if len({round(st.mean(media_k[(i, m)]), 6) for m in ("Hbase", "RLS-f7")}) > 1]
dif.sort(key=lambda i: st.mean(media_k[(i, "Hbase")]) - st.mean(media_k[(i, "RLS-f7")]))
# Formato 16:9: instâncias no eixo x (colunas verticais), para caber num slide.
fig, ax = plt.subplots(figsize=(16, 9))
vals = {i: {m: st.mean(media_k[(i, m)]) for m in ("Hbase", "RLS-f7")} for i in dif}
n_ganha = sum(v["Hbase"] < v["RLS-f7"] for v in vals.values())
for x, i in enumerate(dif):
    v = vals[i]
    ax.plot([x, x], [min(v.values()), max(v.values())], color="#c9c7c0", linewidth=2.5, zorder=1)
    for m, cor in (("RLS-f7", LARANJA), ("Hbase", AZUL)):
        ax.scatter(x, v[m], s=110, color=cor, edgecolor="white", linewidth=1.8, zorder=3, label=m)
topo = max(max(v.values()) for v in vals.values()) * 1.12
ax.axvline(n_ganha - 0.5, color=TEXTO2, linewidth=1, linestyle=(0, (4, 4)))
ax.text(n_ganha / 2 - 0.5, topo * 0.97, f"Hbase melhor ({n_ganha})", ha="center", va="top", fontsize=13,
        color=AZUL, fontweight="bold")
ax.text((n_ganha + len(dif)) / 2 - 0.5, topo * 0.97, f"RLS-f7 melhor ({len(dif) - n_ganha})", ha="center",
        va="top", fontsize=13, color=LARANJA, fontweight="bold")
ax.set_xticks(range(len(dif)), dif, fontsize=12)
ax.set_xlim(-0.6, len(dif) - 0.4)
ax.set_ylim(0, topo)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",") + "%"))
ax.set_ylabel("Desvio médio para LBref nas 10 sementes (menor é melhor)")
ax.grid(axis="y", color=GRADE, linewidth=0.8)
ax.set_axisbelow(True)
ax.tick_params(axis="x", length=0)
h, l = ax.get_legend_handles_labels()
ax.legend([h[1], h[0]], [l[1], l[0]], frameon=False, ncol=2, loc="lower right", bbox_to_anchor=(1, 1.0), fontsize=13)
cabecalho(fig, "Família A: instâncias em que os métodos diferem",
          f"{len(dif)} de {len(inst_a)} instâncias (nas demais, Hbase e RLS-f7 empatam). "
          "Ordenadas da maior vantagem do Hbase (esquerda) à maior vantagem da RLS-f7 (direita).")
fig.subplots_adjust(top=0.89, bottom=0.07, left=0.07, right=0.99)
salva(fig, "figC4_familia_A_por_instancia.png")
