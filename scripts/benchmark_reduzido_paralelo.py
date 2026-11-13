"""Benchmark reduzido (108 execuções) com N processos simultâneos e as mesmas garantias.

Reusa plano, validação, recibos, retomada auditada, trava global, tabela e
integridade de benchmark_reduzido.py. O número de processos e a semente da
ordem entram no contrato: lotes com -j diferentes ou sequenciais não se misturam.
"""

import argparse
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
import math
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import tempfile
import threading
import time

import benchmark_reduzido as base
from executar_experimentos import (RAIZ, METODOS, agora, ambiente, configuracao, conferir,
    esperado, exclusividade, json_atomico, sha)
from piloto import barra_progresso, conferir_prazo
from tabela_comparacao import gravar_tabela
from validar_execucao import exigir, linha_csv, validar

TOTAL = 108


def saida_padrao(jobs):
    return RAIZ/f'results/benchmark_reduzido_j{jobs}/congelada_v2'


def nome(t):
    return f"{t['instancia']}__{t['metodo']}__{t['semente']}"


def ordem(tarefas, semente):
    """Permutação reproduzível sobre a matriz completa (estável na retomada)."""
    nomes = [nome(t) for t in tarefas]
    if semente is not None:
        random.Random(semente).shuffle(nomes)
    return nomes


def plano(jobs, semente_ordem):
    p = base.plano()
    exigir(len(p['tarefas']) == TOTAL, 'Plano incorreto.')
    return {**p, 'uso': 'benchmark_preliminar_TA_sem_H_estrela_paralelo',
            'executor_sha256': sha(Path(__file__)), 'base_sha256': sha(Path(base.__file__)),
            'paralelismo': {'processos': jobs, 'semente_ordem': semente_ordem,
                            'ordem_execucao': ordem(p['tarefas'], semente_ordem)}}


class Lote:
    def __init__(self, p, saida, fd, contrato, digest):
        self.p, self.saida, self.fd, self.contrato, self.digest = p, saida, fd, contrato, digest
        self.cfg_path = saida/'config.cfg'
        self.cfg = configuracao(self.cfg_path)
        self.parar = threading.Event()
        self.filhos = set()
        self.trava_filhos = threading.Lock()

    def encerrar_filhos(self):
        self.parar.set()
        with self.trava_filhos:
            for f in self.filhos:
                if f.poll() is None:
                    f.terminate()

    def rodar(self, t):
        """Executa, valida e publica uma tarefa (roda em thread de trabalho)."""
        d = self.saida/'execucoes'/nome(t)
        pend = self.saida/'.pendentes'
        pend.mkdir(exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix=d.name+'__', dir=pend))
        comando = [str(RAIZ/'bin/tp3'), '--instancia', t['caminho_instancia'], '--metodo', t['metodo'],
                   '--config', str(self.cfg_path), '--semente', str(t['semente']), '--cpu', '60',
                   '--saida', str(temp), '--salvar-solucao']
        inicio = agora()
        with (temp/'stdout.txt').open('w') as out, (temp/'stderr.txt').open('w') as err:
            with self.trava_filhos:
                exigir(not self.parar.is_set(), 'Lote interrompido antes do início.')
                # O filho herda a trava global, como no orquestrador sequencial.
                filho = subprocess.Popen(comando, cwd=RAIZ, stdin=subprocess.DEVNULL, stdout=out,
                                         stderr=err, pass_fds=(self.fd,))
                self.filhos.add(filho)
            try:
                codigo = filho.wait()
            finally:
                with self.trava_filhos:
                    self.filhos.discard(filho)
        exigir(not self.parar.is_set() or codigo == 0, f'Interrompida; tentativa em {temp}')
        exigir(codigo == 0, f'Falha ({codigo}) em {nome(t)}; logs em {temp}')
        exigir(sha(base.CONFIG) == self.p['config_sha256'] == sha(self.cfg_path) and
               sha(RAIZ/'bin/tp3') == self.contrato['ambiente']['executavel_sha256'],
               'Configuração/executável alterado.')
        exigir(sha(Path(t['caminho_instancia'])) == t['sha256_instancia'], 'Instância alterada.')
        resultado, solucao = validar(temp, Path(t['caminho_instancia']), esperado(t, self.cfg_path, 60), self.cfg)
        json_atomico(temp/'concluida.json', dict(versao=1, tarefa=t, contrato_sha256=self.digest,
            inicio_utc=inicio, fim_utc=agora(), codigo_saida=0, comando=comando,
            arquivos={f.name: sha(f) for f in [resultado, solucao]}))
        d.parent.mkdir(parents=True, exist_ok=True)
        temp.rename(d)
        return t


def executar(p, prazo, somente_analisar, saida, jobs):
    with exclusividade(RAIZ/'results/.execucao.lock') as fd:
        conferir_prazo(prazo)
        contrato = {**p, 'ambiente': ambiente()}
        cp = saida/'contrato.json'
        if cp.exists():
            exigir(json.loads(cp.read_text()) == contrato,
                   'Contrato existente difere (máquina/código/configuração/-j/ordem). Não misture protocolos.')
            exigir(sha(saida/'config.cfg') == sha(base.CONFIG), 'Cópia da configuração alterada.')
        else:
            exigir(not somente_analisar, 'Benchmark ainda não executado.')
            exigir(not (saida/'execucoes').exists(), 'Resultados sem contrato.')
            saida.mkdir(parents=True, exist_ok=True)
            (saida/'config.cfg').write_bytes(base.CONFIG.read_bytes())
            json_atomico(saida/'ambiente.json', {'data_utc': agora(), **contrato['ambiente']})
            json_atomico(cp, contrato)
        digest = sha(cp)
        lote = Lote(p, saida, fd, contrato, digest)
        por_nome = {nome(t): t for t in p['tarefas']}

        # Retomada: reaudita tudo que já foi publicado antes de pular.
        pendentes, feitas = [], 0
        for n in p['paralelismo']['ordem_execucao']:
            conferir_prazo(prazo)
            d = saida/'execucoes'/n
            if d.exists():
                conferir(d, por_nome[n], lote.cfg_path, lote.cfg, 60, digest)
                feitas += 1
            else:
                exigir(not somente_analisar, f'Resultado ausente: {d}')
                pendentes.append(por_nome[n])
        if feitas:
            print(f'{feitas} execuções conferidas; {len(pendentes)} pendentes.', flush=True)
            print(barra_progresso(feitas, TOTAL), flush=True)

        erro = None
        fila = iter(pendentes)
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            ativos = set()

            def completar():
                while len(ativos) < jobs and erro is None and not lote.parar.is_set():
                    t = next(fila, None)
                    if t is None:
                        return
                    print(f"[início] {t['instancia']} {t['metodo']} semente {t['semente']}", flush=True)
                    ativos.add(pool.submit(lote.rodar, t))
            try:
                completar()
                while ativos:
                    prontos, _ = wait(ativos, timeout=1, return_when=FIRST_COMPLETED)
                    for f in prontos:
                        ativos.discard(f)
                        try:
                            t = f.result()
                            feitas += 1
                            print(f"[ok] {nome(t)}  {barra_progresso(feitas, TOTAL)}", flush=True)
                        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as e:
                            # Para de iniciar novas; as em andamento terminam e são publicadas.
                            erro = erro or e
                            print(f'Erro: {e}. Aguardando execuções em andamento...', file=sys.stderr, flush=True)
                    conferir_prazo(prazo)
                    completar()
            except BaseException:
                lote.encerrar_filhos()
                wait(ativos)
                raise
        if erro is not None:
            raise erro

        exigir(len(list((saida/'execucoes').iterdir())) == TOTAL, 'Execuções excedentes.')
        conferir_prazo(prazo)
        rows = [linha_csv(next(f for f in (saida/'execucoes'/nome(t)).glob('*.csv')
                               if not f.name.endswith('.solucao.csv'))) for t in p['tarefas']]
        gravar_tabela(saida/'tabela_comparacao.csv', rows, METODOS, {t['instancia'] for t in p['tarefas']}, base.SEMENTES)
        json_atomico(saida/'integridade.json', dict(valido=True, execucoes=TOTAL, contrato_sha256=digest,
            uso=p['uso'], paralelismo={k: v for k, v in p['paralelismo'].items() if k != 'ordem_execucao'},
            familias=dict(Counter(t['familia'] for t in p['tarefas']))))
        print(f'Benchmark reduzido paralelo completo: {TOTAL} soluções validadas. '
              f'Tabela: {saida/"tabela_comparacao.csv"}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-j', '--jobs', type=int, default=max(1, (os.cpu_count() or 2)//2),
                        help='processos simultâneos (padrão: metade dos threads lógicos ~ núcleos físicos)')
    parser.add_argument('--embaralhar', type=int, metavar='SEMENTE', nargs='?', const=1,
                        help='ordem aleatória reproduzível (padrão da semente: 1); sem a opção, ordem do plano')
    parser.add_argument('--max-minutos', type=float, default=60, help='Teto total de parede; padrão 60 minutos.')
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--planejar', action='store_true')
    g.add_argument('--analisar', action='store_true')
    a = parser.parse_args()
    if a.jobs < 1:
        parser.error('-j deve ser positivo.')
    if not math.isfinite(a.max_minutos) or a.max_minutos <= 0:
        parser.error('Teto deve ser positivo e finito.')
    saida = saida_padrao(a.jobs)
    prazo = time.monotonic()+60*a.max_minutos

    def expirar(signum, frame):
        raise TimeoutError('Teto total atingido; resultados completos preservados. Repita o comando para retomar.')
    anterior = signal.signal(signal.SIGALRM, expirar)
    signal.setitimer(signal.ITIMER_REAL, 60*a.max_minutos)
    try:
        p = plano(a.jobs, a.embaralhar)
        if a.planejar:
            print(f'{TOTAL} execuções: 6 instâncias finais × 6 métodos × 3 sementes × até 60 s CPU.')
            print('Instâncias:', ', '.join(dict.fromkeys(t['instancia'] for t in p['tarefas'])))
            print(f'{a.jobs} processos simultâneos; teto ~{math.ceil(TOTAL/a.jobs)} min de parede. '
                  f'Ordem: ' + (f'embaralhada (semente {a.embaralhar})' if a.embaralhar is not None else 'do plano'))
            print('Primeiras:', ', '.join(p['paralelismo']['ordem_execucao'][:a.jobs]))
            print(f'Saída: {saida}')
            return 0
        executar(p, prazo, a.analisar, saida, a.jobs)
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
