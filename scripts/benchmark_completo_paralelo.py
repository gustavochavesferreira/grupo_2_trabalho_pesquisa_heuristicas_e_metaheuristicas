"""Benchmark final completo em paralelo, com H* escolhida no piloto paralelo.

Matriz idêntica à do benchmark.py: 153 instâncias finais × 6 métodos (Hbase, Hext,
Hint, Hcomb, Haleat, RLS-f7) × 10 sementes comuns = 9180 execuções de até 60 s de CPU.

Solução inicial (--inicial, padrão aleatoria): na aleatória, as propostas e o Haleat
partem da mesma inicial aleatória da RLS-f7 (--inicial aleatoria, mesma semente), o
que torna a comparação com a RLS-f7 justa; a RLS-f7 é idêntica nas duas variantes.
Na gulosa, as propostas e o Haleat partem da construção gulosa (padrão do executável).

H* vem do lote do piloto paralelo com a MESMA inicial
(results/piloto_paralelo_s10_j6/<inicial>), reauditado por inteiro a cada chamada,
inclusive o comando de cada recibo, e escolhido pela regra do piloto.py: menor
desvio médio exato, maior alcance de LBref, menor mediana de tempo até o melhor K;
empate total preserva a ordem Hbase, Hext, Hint, Hcomb. A escolha e o contrato do
piloto entram no contrato deste lote. Não grava config/h_estrela_v2.json: o caminho
sequencial (piloto.py + benchmark.py) permanece independente.

Mesmas garantias do benchmark estendido: contrato, validação completa de cada
solução, recibos, retomada auditada, trava global, núcleos físicos fixos e ordem
sorteada.
"""

import argparse
from collections import Counter
import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time

import benchmark_reduzido as base
import benchmark_reduzido_paralelo as par
import piloto_paralelo as pp
from executar_experimentos import (RAIZ, METODOS, PROPOSTAS, SEMENTES, conferir, configuracao, json_atomico,
                                   ler_manifesto, sha)
from validar_execucao import exigir, linha_csv
from verificar_congelamento import verificar

TOTAL = 9180
FAMILIAS = {'A': 2280, 'BENG': 600, 'CLASS': 6300}
CRITERIO = ['menor_desvio_medio', 'maior_alcance_lb', 'menor_tempo_melhor_mediano']


INICIAIS = ['aleatoria', 'gulosa']
ARGS_INICIAL = {'gulosa': [], 'aleatoria': ['--inicial', 'aleatoria']}


def lote_piloto(inicial, jobs_piloto=6):
    return pp.saida_lote(inicial, len(SEMENTES), jobs_piloto)


def saida_padrao(jobs, inicial):
    return RAIZ/f'results/benchmark_completo_paralelo_j{jobs}/{inicial}/congelada_v2'


def args_tarefa(metodo, inicial):
    # A RLS-f7 já parte de uma inicial aleatória e o executável recusa --inicial para ela.
    return [] if metodo == 'RLS-f7' else ARGS_INICIAL[inicial]


def resumir(metodo, linhas):
    desvio = sum((Fraction(100*(int(r['K'])-int(r['LBref'])), int(r['LBref'])) for r in linhas), Fraction())/len(linhas)
    return {'metodo': metodo, 'execucoes': len(linhas), 'K_medio': statistics.mean(int(r['K']) for r in linhas),
            'desvio_medio': float(desvio), 'desvio_exato': str(desvio),
            'alcances_lb': sum(int(r['alcancou_lb']) for r in linhas),
            'tempo_melhor_mediano': statistics.median(float(r['tempo_melhor']) for r in linhas)}


def criterio(r):
    return Fraction(r['desvio_exato']), -r['alcances_lb'], r['tempo_melhor_mediano']


def selecionar_h_estrela(lote, inicial, sementes=SEMENTES, manifesto=RAIZ/'instances/manifests/piloto.csv'):
    """Audita o lote do piloto paralelo da inicial dada por inteiro e aplica a regra de H* do piloto.py."""
    cp = lote/'contrato.json'
    exigir(cp.is_file(), f'Piloto paralelo ({inicial}) não encontrado: {lote}')
    contrato = json.loads(cp.read_text())
    exigir(contrato['uso'] == f'piloto_paralelo_exploratorio_sem_H_estrela_inicial_{inicial}'
           and contrato['inicial'] == inicial and contrato['args_extras'] == ARGS_INICIAL[inicial]
           and contrato['cpu'] == 60, f'Lote não é o piloto paralelo com inicial {inicial} e 60 s de CPU.')
    exigir(contrato['config_sha256'] == sha(base.CONFIG) == sha(lote/'config.cfg'), 'Configuração difere da congelada.')
    exigir(contrato['sementes_sha256'] == sha(RAIZ/'config/sementes.txt'), 'Sementes divergentes.')
    exigir(contrato['manifestos']['piloto'] == sha(manifesto), 'Manifesto do piloto alterado.')
    exigir(contrato['metodos'] == PROPOSTAS and contrato['sementes'] == list(sementes), 'Métodos/sementes do piloto divergentes.')
    ids = {r['identificador'] for r in ler_manifesto(manifesto)}
    tarefas = contrato['tarefas']
    esperadas = {(i, m, s) for i in ids for m in PROPOSTAS for s in sementes}
    exigir(len(tarefas) == len(esperadas) and {(t['instancia'], t['metodo'], t['semente']) for t in tarefas} == esperadas,
           'Matriz do piloto incompleta, duplicada ou incorreta.')
    exigir({p.name for p in (lote/'execucoes').iterdir()} == {par.nome(t) for t in tarefas}, 'Execuções do piloto ausentes ou excedentes.')
    digest = sha(cp)
    integ = json.loads((lote/'integridade.json').read_text())
    exigir(integ['valido'] and integ['contrato_sha256'] == digest and integ['execucoes'] == len(tarefas),
           'Integridade do piloto ausente ou divergente.')
    cfg = configuracao(lote/'config.cfg')
    linhas = []
    for n, t in enumerate(tarefas, 1):
        pasta = lote/'execucoes'/par.nome(t)
        conferir(pasta, t, lote/'config.cfg', cfg, 60, digest)
        comando = json.loads((pasta/'concluida.json').read_text())['comando']
        exigir(('--inicial' not in comando if inicial == 'gulosa' else comando[-2:] == ARGS_INICIAL[inicial]),
               f'Recibo com solução inicial divergente: {pasta.name}')
        linhas.append(linha_csv(next(f for f in pasta.glob('*.csv') if not f.name.endswith('.solucao.csv'))))
        if n % 100 == 0 or n == len(tarefas):
            print(f'Piloto paralelo auditado: {n}/{len(tarefas)}.', flush=True)
    resumos = [resumir(m, [r for r in linhas if r['metodo'] == m]) for m in PROPOSTAS]
    melhor = min(criterio(r) for r in resumos)
    empatadas = [r['metodo'] for r in resumos if criterio(r) == melhor]
    return {'H_estrela': empatadas[0], 'empate_total': empatadas, 'criterio': CRITERIO,
            'desempate_final': 'ordem Hbase, Hext, Hint, Hcomb somente se os três critérios forem idênticos',
            'inicial': inicial, 'origem': f'piloto paralelo, inicial {inicial} (aceito pelo grupo como piloto válido)',
            'piloto_lote': str(lote.relative_to(RAIZ)) if lote.is_relative_to(RAIZ) else str(lote),
            'piloto_contrato_sha256': digest, 'execucoes_validas': len(tarefas), 'resumos': resumos}


def plano(jobs, semente_ordem, selo, inicial):
    verificar()
    final = ler_manifesto(RAIZ/'instances/manifests/final.csv')
    tarefas = []
    for r in final:
        origem = (RAIZ/'instances/source'/r['caminho']).resolve()
        exigir(origem.is_relative_to((RAIZ/'instances/source').resolve()) and sha(origem) == r['sha256'],
               f'Instância ausente/alterada: {r["identificador"]}')
        for m in METODOS:
            for s in SEMENTES:
                tarefas.append(dict(instancia=r['identificador'], familia=r['familia'], metodo=m, semente=s,
                                    caminho_instancia=str(origem), sha256_instancia=r['sha256'],
                                    args_extras=args_tarefa(m, inicial)))
    exigir(selo['inicial'] == inicial, 'H* foi escolhida com outra solução inicial.')
    exigir(len(tarefas) == TOTAL and dict(Counter(t['familia'] for t in tarefas)) == FAMILIAS,
           'Matriz final incorreta.')
    return dict(uso=f'benchmark_completo_paralelo_H_estrela_piloto_paralelo_inicial_{inicial}', cpu=60,
                tarefas=tarefas, sementes=list(SEMENTES), metodos=list(METODOS), inicial=inicial, h_estrela=selo,
                config_sha256=sha(base.CONFIG), sementes_sha256=sha(RAIZ/'config/sementes.txt'),
                manifestos={n: sha(RAIZ/f'instances/manifests/{n}.csv') for n in ['piloto', 'final']},
                executor_sha256=sha(Path(__file__)), paralelo_sha256=sha(Path(par.__file__)),
                paralelismo={'processos': jobs, 'semente_ordem': semente_ordem, 'cpus': par.cpus_para(jobs),
                             'ordem_execucao': par.ordem(tarefas, semente_ordem)})


def p_sinais(vitorias, derrotas):
    """Teste dos sinais exato bilateral (empates descartados)."""
    n = vitorias+derrotas
    if n == 0:
        return 1.0
    cauda = sum(math.comb(n, k) for k in range(min(vitorias, derrotas)+1))/2**n
    return min(1.0, 2*cauda)


def comparar_h_estrela(saida, p):
    """Comparações pareadas (instância, semente) de H* contra cada outro método, por K."""
    h = p['h_estrela']['H_estrela']
    K = {}
    for t in p['tarefas']:
        r = linha_csv(next(f for f in (saida/'execucoes'/par.nome(t)).glob('*.csv') if not f.name.endswith('.solucao.csv')))
        K[(t['instancia'], t['semente'], t['metodo'])] = int(r['K'])
    pares = sorted({(i, s) for i, s, _ in K})
    linhas = []
    for m in p['metodos']:
        if m == h:
            continue
        v = sum(K[(i, s, h)] < K[(i, s, m)] for i, s in pares)
        d = sum(K[(i, s, h)] > K[(i, s, m)] for i, s in pares)
        linhas.append(dict(H_estrela=h, outro=m, pares=len(pares), vitorias_H=v, empates=len(pares)-v-d,
                           derrotas_H=d, p_sinais_bilateral=p_sinais(v, d)))
    with (saida/'comparacoes_h_estrela.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)
    return linhas


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-j', '--jobs', type=int, default=len(par.nucleos_fisicos()),
                        help='processos simultâneos, cada um fixo num núcleo físico (padrão: todos os núcleos físicos)')
    parser.add_argument('--embaralhar', type=int, metavar='SEMENTE', nargs='?', const=1,
                        help='ordem aleatória reproduzível (padrão da semente: 1); sem a opção, ordem do plano')
    parser.add_argument('--max-minutos', type=float, help='Teto de parede desta chamada; padrão: sem teto.')
    parser.add_argument('--inicial', choices=INICIAIS, default='aleatoria',
                        help='solução inicial das propostas e do Haleat; H* vem do piloto com a mesma inicial '
                             '(padrão: aleatoria, a mesma partida da RLS-f7)')
    parser.add_argument('--piloto', type=Path,
                        help='lote do piloto paralelo (padrão: results/piloto_paralelo_s10_j6/<inicial>/congelada_v2)')
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--planejar', action='store_true')
    g.add_argument('--analisar', action='store_true')
    a = parser.parse_args()
    if a.jobs < 1:
        parser.error('-j deve ser positivo.')
    if a.max_minutos is not None and (not math.isfinite(a.max_minutos) or a.max_minutos <= 0):
        parser.error('Teto deve ser positivo e finito.')
    saida = saida_padrao(a.jobs, a.inicial)
    piloto = (a.piloto or lote_piloto(a.inicial)).resolve()
    prazo = None
    anterior = None
    if a.max_minutos is not None:
        prazo = time.monotonic()+60*a.max_minutos

        def expirar(signum, frame):
            raise TimeoutError('Teto total atingido; resultados completos preservados. Repita o comando para retomar.')
        anterior = signal.signal(signal.SIGALRM, expirar)
        signal.setitimer(signal.ITIMER_REAL, 60*a.max_minutos)
    try:
        selo = selecionar_h_estrela(piloto, a.inicial)
        print(f"H* = {selo['H_estrela']} (piloto paralelo, inicial {a.inicial}; empatadas: {', '.join(selo['empate_total'])})", flush=True)
        for r in selo['resumos']:
            print(f"  {r['metodo']:6} desvio médio {r['desvio_medio']:.3f}%  alcances LBref {r['alcances_lb']}/{r['execucoes']}", flush=True)
        p = plano(a.jobs, a.embaralhar, selo, a.inicial)
        if a.planejar:
            print(f'{TOTAL} execuções: 153 instâncias finais × 6 métodos × 10 sementes × até 60 s CPU '
                  f'(A 2280, BENG 600, CLASS 6300). Inicial: {a.inicial} '
                  + ('(propostas e Haleat com --inicial aleatoria; RLS-f7 inalterada).' if a.inicial == 'aleatoria'
                     else '(construção gulosa; RLS-f7 parte do aleatório).'))
            print(f'{a.jobs} processos em núcleos físicos {p["paralelismo"]["cpus"]}; teto nominal '
                  f'~{math.ceil(TOTAL/a.jobs)} min (~{TOTAL/a.jobs/60:.1f} h) de parede. Ordem: '
                  + (f'embaralhada (semente {a.embaralhar})' if a.embaralhar is not None else 'do plano'))
            print(f'Saída: {saida}')
            return 0
        par.executar(p, prazo, a.analisar, saida, a.jobs)
        json_atomico(saida/'h_estrela.json', selo)
        for c in comparar_h_estrela(saida, p):
            print(f"{c['H_estrela']} vs {c['outro']}: {c['vitorias_H']} vitórias, {c['empates']} empates, "
                  f"{c['derrotas_H']} derrotas (p sinais = {c['p_sinais_bilateral']:.3g})")
        print(f'H*: {saida/"h_estrela.json"}; comparações: {saida/"comparacoes_h_estrela.csv"}')
    except TimeoutError as e:
        print(str(e), file=sys.stderr); return 124
    except KeyboardInterrupt:
        print('Interrompido; repita o mesmo comando para retomar.', file=sys.stderr); return 130
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as e:
        print(f'Erro: {e}. Resultados completos preservados.', file=sys.stderr); return 1
    finally:
        if anterior is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, anterior)
    return 0


if __name__ == '__main__':
    sys.exit(main())
