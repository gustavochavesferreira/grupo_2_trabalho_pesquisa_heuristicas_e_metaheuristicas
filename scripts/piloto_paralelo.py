"""Piloto paralelo exploratório: matriz do piloto (10 instâncias × 4 propostas × 10 sementes)
partindo da construção gulosa e da inicial aleatória da RLS-f7.

Executa dois lotes em sequência, um por solução inicial, cada um com contrato,
validação completa, recibos, retomada auditada, trava global, núcleos físicos
fixos e ordem sorteada (mesmas garantias do benchmark estendido). NÃO é o piloto
formal: não seleciona nem grava H*, e não substitui scripts/piloto.py.
"""

import argparse
import math
from pathlib import Path
import signal
import subprocess
import sys
import time

import benchmark_reduzido as base
import benchmark_reduzido_paralelo as par
from executar_experimentos import RAIZ, PROPOSTAS, SEMENTES, ler_manifesto, sha
from validar_execucao import exigir
from verificar_congelamento import verificar

INICIAIS = ['gulosa', 'aleatoria']


def saida_lote(inicial, n_sementes, jobs):
    return RAIZ/f'results/piloto_paralelo_s{n_sementes}_j{jobs}/{inicial}/congelada_v2'


def plano(jobs, semente_ordem, n_sementes, inicial):
    verificar()
    exigir(inicial in INICIAIS, 'Inicial deve ser gulosa ou aleatoria.')
    exigir(1 <= n_sementes <= len(SEMENTES), f'Use de 1 a {len(SEMENTES)} sementes.')
    sementes = SEMENTES[:n_sementes]
    piloto = ler_manifesto(RAIZ/'instances/manifests/piloto.csv')
    exigir(len(piloto) == 10, 'Manifesto do piloto deve ter dez instâncias.')
    tarefas = []
    for r in piloto:
        origem = (RAIZ/'instances/source'/r['caminho']).resolve()
        exigir(origem.is_relative_to((RAIZ/'instances/source').resolve()) and sha(origem) == r['sha256'],
               f'Instância ausente/alterada: {r["identificador"]}')
        for m in PROPOSTAS:
            for s in sementes:
                tarefas.append(dict(instancia=r['identificador'], familia=r['familia'], metodo=m, semente=s,
                                    caminho_instancia=str(origem), sha256_instancia=r['sha256']))
    # A gulosa é o comportamento padrão do executável; a aleatória passa --inicial.
    args = [] if inicial == 'gulosa' else ['--inicial', inicial]
    return dict(uso=f'piloto_paralelo_exploratorio_sem_H_estrela_inicial_{inicial}', cpu=60, tarefas=tarefas,
                sementes=sementes, metodos=list(PROPOSTAS), inicial=inicial, args_extras=args,
                config_sha256=sha(base.CONFIG), sementes_sha256=sha(RAIZ/'config/sementes.txt'),
                manifestos={n: sha(RAIZ/f'instances/manifests/{n}.csv') for n in ['piloto', 'final']},
                executor_sha256=sha(Path(__file__)), paralelo_sha256=sha(Path(par.__file__)),
                paralelismo={'processos': jobs, 'semente_ordem': semente_ordem, 'cpus': par.cpus_para(jobs),
                             'ordem_execucao': par.ordem(tarefas, semente_ordem)})


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-j', '--jobs', type=int, default=len(par.nucleos_fisicos()),
                        help='processos simultâneos, cada um fixo num núcleo físico (padrão: todos os núcleos físicos)')
    parser.add_argument('--embaralhar', type=int, metavar='SEMENTE', nargs='?', const=1,
                        help='ordem aleatória reproduzível (padrão da semente: 1); sem a opção, ordem do plano')
    parser.add_argument('--sementes', type=int, default=10, help='quantas sementes comuns usar (1001..), padrão 10')
    parser.add_argument('--iniciais', nargs='+', choices=INICIAIS, default=INICIAIS,
                        help='soluções iniciais, executadas nesta ordem (padrão: gulosa aleatoria)')
    parser.add_argument('--max-minutos', type=float,
                        help='Teto total de parede da chamada (todos os lotes); padrão: teto nominal + 30 min.')
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--planejar', action='store_true')
    g.add_argument('--analisar', action='store_true')
    a = parser.parse_args()
    if a.jobs < 1:
        parser.error('-j deve ser positivo.')
    try:
        planos = [(i, plano(a.jobs, a.embaralhar, a.sementes, i)) for i in a.iniciais]
    except (OSError, ValueError, KeyError) as e:
        print(f'Erro: {e}', file=sys.stderr); return 1
    total = sum(len(p['tarefas']) for _, p in planos)
    nominal = math.ceil(total/a.jobs)
    max_minutos = a.max_minutos if a.max_minutos is not None else nominal + 30
    if not math.isfinite(max_minutos) or max_minutos <= 0:
        parser.error('Teto deve ser positivo e finito.')
    if a.planejar:
        for i, p in planos:
            print(f'[{i}] {len(p["tarefas"])} execuções: 10 instâncias do piloto × {len(p["metodos"])} métodos × '
                  f'{len(p["sementes"])} sementes × até 60 s CPU -> {saida_lote(i, a.sementes, a.jobs)}')
        print(f'Total {total} execuções; {a.jobs} processos em núcleos físicos {planos[0][1]["paralelismo"]["cpus"]}; '
              f'teto nominal ~{nominal} min (--max-minutos {max_minutos:g}). Ordem: '
              + (f'embaralhada (semente {a.embaralhar})' if a.embaralhar is not None else 'do plano'))
        print('Exploratório: não seleciona nem grava H*.')
        return 0
    prazo = time.monotonic()+60*max_minutos

    def expirar(signum, frame):
        raise TimeoutError('Teto total atingido; resultados completos preservados. Repita o comando para retomar.')
    anterior = signal.signal(signal.SIGALRM, expirar)
    signal.setitimer(signal.ITIMER_REAL, 60*max_minutos)
    try:
        for i, p in planos:
            print(f'=== Lote: inicial {i} ===', flush=True)
            par.executar(p, prazo, a.analisar, saida_lote(i, a.sementes, a.jobs), a.jobs)
    except TimeoutError as e:
        print(str(e), file=sys.stderr); return 124
    except KeyboardInterrupt:
        print('Interrompido; repita o mesmo comando para retomar.', file=sys.stderr); return 130
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as e:
        print(f'Erro: {e}. Resultados completos preservados.', file=sys.stderr); return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, anterior)
    return 0


if __name__ == '__main__':
    sys.exit(main())
