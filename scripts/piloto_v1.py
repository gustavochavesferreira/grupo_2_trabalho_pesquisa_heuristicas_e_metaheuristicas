"""Piloto preliminar reduzido para a V1 do TA; não seleciona H* oficial."""

import argparse
from collections import Counter
import csv
import json
import math
import statistics
import subprocess
import sys
import time

from executar_experimentos import RAIZ, PROPOSTAS, configuracao, conferir, exclusividade, sha
from piloto import executar_com_progresso, conferir_prazo
from validar_execucao import exigir, linha_csv
from verificar_congelamento import verificar

IDS = ['A14', 'cl_07_060_02', 'cl_09_060_02']
EXTRAS = ['A23', 'cl_03_060_02']
SEMENTES = [1001, 1002, 1003]
SAIDA = RAIZ / 'results/ta_v1'
CONFIG = RAIZ / 'config/congelada_v2.cfg'


def comando(ids=None, saida=None):
    ids = IDS if ids is None else ids
    saida = SAIDA if saida is None else saida
    return [sys.executable, '-B', str(RAIZ / 'scripts/executar_experimentos.py'),
            '--modo', 'calibration', '--config', str(CONFIG), '--cpu', '60',
            '--saida', str(saida), '--instancias', *ids,
            '--sementes', *map(str, SEMENTES)]


def plano(ids=None, saida=None):
    ids = IDS if ids is None else ids
    verificar()
    p = json.loads(subprocess.check_output(comando(ids,saida)+['--planejar'], cwd=RAIZ, text=True))
    esperadas = {(i, m, s) for i in ids for m in PROPOSTAS for s in SEMENTES}
    exigir(p['cpu'] == 60 and len(p['tarefas']) == len(esperadas) and
           {(t['instancia'],t['metodo'],t['semente']) for t in p['tarefas']} == esperadas,
           'Plano reduzido incorreto.')
    return p


def analisar(p, prazo, ids=None, saida=None):
    ids = IDS if ids is None else ids
    saida = SAIDA if saida is None else saida
    with exclusividade(RAIZ / 'results/.execucao.lock'):
        conferir_prazo(prazo)
        lote = saida / 'calibration/congelada_v2'
        cp = lote / 'contrato.json'
        c = json.loads(cp.read_text())
        exigir(c['tarefas'] == p['tarefas'] and c['cpu'] == 60 and c['modo'] == 'calibration', 'Contrato divergente.')
        exigir(c['config_sha256'] == sha(CONFIG) == sha(lote/'config.cfg'), 'Configuração alterada.')
        exigir(c['sementes_sha256'] == sha(RAIZ/'config/sementes.txt'), 'Sementes alteradas.')
        for n in ['piloto', 'final']:
            exigir(c['manifestos'][n] == sha(RAIZ/f'instances/manifests/{n}.csv'), 'Manifesto alterado.')
        cfg = configuracao(lote/'config.cfg')
        nomes = {'__'.join(str(t[k]) for k in ['instancia','metodo','semente']) for t in p['tarefas']}
        exigir({d.name for d in (lote/'execucoes').iterdir()} == nomes, 'Matriz incompleta ou excedente.')
        rows = []
        for t in p['tarefas']:
            conferir_prazo(prazo)
            d = lote/'execucoes'/'__'.join(str(t[k]) for k in ['instancia','metodo','semente'])
            conferir(d,t,lote/'config.cfg',cfg,60,sha(cp))
            rows.append(linha_csv(next(f for f in d.glob('*.csv') if not f.name.endswith('.solucao.csv'))))
        resumos = []
        for i in ids:
            for m in PROPOSTAS:
                rs = [r for r in rows if r['instancia'] == i and r['metodo'] == m]
                exigir(len(rs) == 3, 'Comparação incompleta.')
                paradas = Counter(r['motivo_parada'] for r in rs)
                resumos.append(dict(instancia=i, metodo=m, sementes=3, LBref=int(rs[0]['LBref']),
                    K_medio=statistics.mean(int(r['K']) for r in rs), K_melhor=min(int(r['K']) for r in rs),
                    K_pior=max(int(r['K']) for r in rs), desvio_medio=statistics.mean(float(r['desvio']) for r in rs),
                    cpu_media=statistics.mean(float(r['tempo_total']) for r in rs),
                    tempo_melhor_mediano=statistics.median(float(r['tempo_melhor']) for r in rs),
                    alcances_lb=sum(int(r['alcancou_lb']) for r in rs),
                    paradas_cpu=paradas['limite_cpu'], paradas_reparo=paradas['orcamento_reparo']))
        with (saida/'resumo.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(resumos[0]));w.writeheader();w.writerows(resumos)
        (saida/'integridade.json').write_text(json.dumps(dict(valido=True,execucoes=len(rows),
            uso='preliminar_TA_nao_substitui_piloto_formal_nao_seleciona_H_estrela',contrato_sha256=sha(cp)),indent=2)+'\n')
        print(f'Bloco concluído: {len(rows)} soluções validadas. Resumo: {saida / "resumo.csv"}')
        return resumos, c['ambiente'], sha(cp)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-minutos',type=float,default=75,help='Teto total da chamada; padrão 75 minutos.')
    grupo=parser.add_mutually_exclusive_group()
    grupo.add_argument('--planejar',action='store_true')
    grupo.add_argument('--analisar',action='store_true')
    a=parser.parse_args()
    if not math.isfinite(a.max_minutos) or a.max_minutos<=0:
        parser.error('--max-minutos deve ser positivo e finito.')
    prazo=time.monotonic()+60*a.max_minutos
    try:
        blocos = [(IDS, SAIDA), (EXTRAS, RAIZ/'results/ta_v1_extra')]
        planos = [plano(ids,saida) for ids,saida in blocos]
        if a.planejar:
            print('Piloto V1 ampliado: 5 instâncias × 4 métodos × 3 sementes = 60 execuções, até 60 s de CPU cada.')
            print('Blocos retomáveis: 36 originais + 24 adicionais. Instâncias:',', '.join(IDS+EXTRAS))
            return 0
        resumos, ambientes, contratos = [], [], []
        for n, ((ids,saida),p) in enumerate(zip(blocos,planos),1):
            print(f'Bloco {n}/2 ({len(p["tarefas"])} execuções).',flush=True)
            if not a.analisar:
                executar_com_progresso(comando(ids,saida),prazo)
            rs,env,digest = analisar(p,prazo,ids,saida)
            resumos.extend(rs);ambientes.append(env);contratos.append(digest)
        exigir(ambientes[0] == ambientes[1], 'Não combinar blocos com código/ambientes diferentes.')
        conferir_prazo(prazo)
        with (SAIDA/'resumo_ampliado.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(resumos[0]));w.writeheader();w.writerows(resumos)
        (SAIDA/'integridade_ampliado.json').write_text(json.dumps(dict(valido=True,execucoes=60,
            uso='preliminar_TA_nao_seleciona_H_estrela',contratos_sha256=contratos),indent=2)+'\n')
        print(f'Piloto V1 ampliado concluído: 60 soluções validadas. Tabela: {SAIDA / "resumo_ampliado.csv"}')
    except TimeoutError as e:
        print(str(e),file=sys.stderr);return 124
    except KeyboardInterrupt:
        print('Interrompido; repita o comando para retomar.',file=sys.stderr);return 130
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as e:
        print(f'Erro: {e}. Resultados completos preservados.',file=sys.stderr);return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
