"""Tabela descritiva geral de uma matriz completa e pareada de resultados."""

import csv
import statistics
from validar_execucao import exigir


def gravar_tabela(caminho, linhas, metodos, instancias, sementes):
    esperadas = {(i,m,str(s)) for i in instancias for m in metodos for s in sementes}
    chaves = [(r['instancia'],r['metodo'],r['semente']) for r in linhas]
    exigir(len(chaves) == len(esperadas) and set(chaves) == esperadas,
           'Tabela exige matriz completa, pareada e sem duplicatas.')
    limites = {}
    for r in linhas:
        exigir(limites.setdefault(r['instancia'],r['LBref']) == r['LBref'], 'LBref inconsistente entre métodos.')
    tabela = []
    for metodo in metodos:
        rs = [r for r in linhas if r['metodo'] == metodo]
        tabela.append(dict(metodo=metodo, instancias=len(instancias), execucoes=len(rs),
            K_medio=statistics.mean(int(r['K']) for r in rs),
            desvio_medio_pct=statistics.mean(float(r['desvio']) for r in rs),
            desvio_mediano_pct=statistics.median(float(r['desvio']) for r in rs),
            alcance_LBref_pct=100*statistics.mean(int(r['alcancou_lb']) for r in rs),
            tempo_melhor_mediano_s=statistics.median(float(r['tempo_melhor']) for r in rs),
            CPU_media_s=statistics.mean(float(r['tempo_total']) for r in rs),
            paradas_CPU=sum(r['motivo_parada']=='limite_cpu' for r in rs),
            paradas_reparo=sum(r['motivo_parada']=='orcamento_reparo' for r in rs)))
    with caminho.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(tabela[0]));w.writeheader();w.writerows(tabela)
    return tabela
