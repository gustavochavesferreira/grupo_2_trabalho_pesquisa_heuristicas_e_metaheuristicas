"""Benchmark estendido: instâncias de config/benchmark_estendido.txt × seis métodos × sementes comuns.

Mesmas garantias do benchmark reduzido paralelo: contrato, validação completa,
recibos, retomada auditada, trava global herdada, tabela e integridade. A lista,
as sementes, o número de processos e a ordem entram no contrato.
"""

import argparse
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import benchmark_reduzido as base
import benchmark_reduzido_paralelo as par
from executar_experimentos import RAIZ, METODOS, SEMENTES, ler_manifesto, sha
from validar_execucao import exigir
from verificar_congelamento import verificar

LISTA = RAIZ/'config/benchmark_estendido.txt'


def ler_lista(caminho):
    ids = [l.strip() for l in caminho.read_text().splitlines() if l.strip() and not l.strip().startswith('#')]
    exigir(ids and len(set(ids)) == len(ids), 'Lista vazia ou com instâncias repetidas.')
    return ids


def plano(jobs, semente_ordem, n_sementes, lista=LISTA):
    verificar()
    exigir(1 <= n_sementes <= len(SEMENTES), f'Use de 1 a {len(SEMENTES)} sementes.')
    sementes = SEMENTES[:n_sementes]
    ids = ler_lista(lista)
    final = {r['identificador']: r for r in ler_manifesto(RAIZ/'instances/manifests/final.csv')}
    piloto = {r['identificador'] for r in ler_manifesto(RAIZ/'instances/manifests/piloto.csv')}
    fora = [i for i in ids if i not in final]
    exigir(not fora, f'Instâncias fora do manifesto final: {", ".join(fora)}')
    exigir(not set(ids) & piloto, 'Interseção com piloto.')
    tarefas = []
    for i in ids:
        r = final[i]
        origem = (RAIZ/'instances/source'/r['caminho']).resolve()
        exigir(origem.is_relative_to((RAIZ/'instances/source').resolve()) and sha(origem) == r['sha256'],
               f'Instância ausente/alterada: {i}')
        for m in METODOS:
            for s in sementes:
                tarefas.append(dict(instancia=i, familia=r['familia'], metodo=m, semente=s,
                                    caminho_instancia=str(origem), sha256_instancia=r['sha256']))
    return dict(uso='benchmark_estendido_TA_sem_H_estrela', cpu=60, tarefas=tarefas, sementes=sementes,
                lista=ids, lista_sha256=sha(lista), config_sha256=sha(base.CONFIG),
                sementes_sha256=sha(RAIZ/'config/sementes.txt'),
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
    parser.add_argument('--sementes', type=int, default=3, help='quantas sementes comuns usar (1001..), padrão 3')
    parser.add_argument('--max-minutos', type=float, help='Teto total de parede; padrão: teto nominal + 30 min.')
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--planejar', action='store_true')
    g.add_argument('--analisar', action='store_true')
    a = parser.parse_args()
    if a.jobs < 1:
        parser.error('-j deve ser positivo.')
    saida = RAIZ/f'results/benchmark_estendido_s{a.sementes}_j{a.jobs}/congelada_v2'
    try:
        p = plano(a.jobs, a.embaralhar, a.sementes)
    except (OSError, ValueError, KeyError) as e:
        print(f'Erro: {e}', file=sys.stderr); return 1
    total = len(p['tarefas'])
    nominal = math.ceil(total/a.jobs)
    max_minutos = a.max_minutos if a.max_minutos is not None else nominal + 30
    if not math.isfinite(max_minutos) or max_minutos <= 0:
        parser.error('Teto deve ser positivo e finito.')
    if a.planejar:
        print(f'{total} execuções: {len(p["lista"])} instâncias finais × {len(METODOS)} métodos × '
              f'{len(p["sementes"])} sementes × até 60 s CPU.')
        print('Instâncias:', ', '.join(p['lista']))
        print(f'{a.jobs} processos simultâneos; teto nominal ~{nominal} min de parede '
              f'(--max-minutos {max_minutos:g}). Ordem: '
              + (f'embaralhada (semente {a.embaralhar})' if a.embaralhar is not None else 'do plano'))
        print('CPUs lógicas (uma por núcleo físico):', p['paralelismo']['cpus'])
        print(f'Saída: {saida}')
        return 0
    prazo = time.monotonic()+60*max_minutos

    def expirar(signum, frame):
        raise TimeoutError('Teto total atingido; resultados completos preservados. Repita o comando para retomar.')
    anterior = signal.signal(signal.SIGALRM, expirar)
    signal.setitimer(signal.ITIMER_REAL, 60*max_minutos)
    try:
        par.executar(p, prazo, a.analisar, saida, a.jobs)
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
