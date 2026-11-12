"""Benchmark preliminar dos seis métodos: 108 execuções, sem selecionar H*."""

import argparse
from collections import Counter
import json
import math
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from executar_experimentos import (RAIZ, METODOS, agora, ambiente, configuracao,
    conferir, exclusividade, esperado, json_atomico, ler_manifesto, processo, sha)
from piloto import barra_progresso, conferir_prazo
from tabela_comparacao import gravar_tabela
from validar_execucao import exigir, linha_csv, validar
from verificar_congelamento import verificar

SEMENTES = [1001,1002,1003]
CONFIG = RAIZ/'config/congelada_v2.cfg'
SAIDA = RAIZ/'results/benchmark_reduzido/congelada_v2'


def selecionar(final):
    saida = []
    for familia in ['A','BENG']:
        rs = sorted((r for r in final if r['familia']==familia),key=lambda r:(int(r['total_copias']),r['identificador']))
        exigir(len(rs)>=3,'Família sem instâncias suficientes.')
        saida.extend([rs[len(rs)//3],rs[2*len(rs)//3]])
    for classe in [3,7]:
        rs=[r for r in final if r['familia']=='CLASS' and int(r['classe'])==classe
            and int(r['tamanho'])==100 and int(r['replica'])==1]
        exigir(len(rs)==1,'CLASS ausente ou duplicada.');saida.extend(rs)
    return saida


def plano():
    verificar()
    piloto=ler_manifesto(RAIZ/'instances/manifests/piloto.csv')
    instancias=selecionar(ler_manifesto(RAIZ/'instances/manifests/final.csv'))
    exigir(not {r['identificador'] for r in piloto}&{r['identificador'] for r in instancias},'Interseção com piloto.')
    tarefas=[]
    for r in instancias:
        origem=(RAIZ/'instances/source'/r['caminho']).resolve()
        exigir(origem.is_relative_to((RAIZ/'instances/source').resolve()) and sha(origem)==r['sha256'],'Instância ausente/alterada.')
        for m in METODOS:
            for s in SEMENTES:
                tarefas.append(dict(instancia=r['identificador'],familia=r['familia'],metodo=m,semente=s,
                    caminho_instancia=str(origem),sha256_instancia=r['sha256']))
    exigir(len(tarefas)==108,'Plano incorreto.')
    return dict(uso='benchmark_preliminar_TA_sem_H_estrela',cpu=60,tarefas=tarefas,
        config_sha256=sha(CONFIG),sementes_sha256=sha(RAIZ/'config/sementes.txt'),
        manifestos={n:sha(RAIZ/f'instances/manifests/{n}.csv') for n in ['piloto','final']},
        executor_sha256=sha(Path(__file__)))


def executar(p, prazo, somente_analisar):
    with exclusividade(RAIZ/'results/.execucao.lock') as fd:
        conferir_prazo(prazo)
        cfg=configuracao(CONFIG)
        contrato={**p,'ambiente':ambiente()}
        cp=SAIDA/'contrato.json'
        if cp.exists():
            exigir(json.loads(cp.read_text())==contrato,'Contrato existente difere de máquina/código/configuração. Não misture ambientes.')
            exigir(sha(SAIDA/'config.cfg')==sha(CONFIG),'Cópia da configuração alterada.')
        else:
            exigir(not somente_analisar,'Benchmark ainda não executado.')
            exigir(not (SAIDA/'execucoes').exists(),'Resultados sem contrato.')
            SAIDA.mkdir(parents=True,exist_ok=True)
            (SAIDA/'config.cfg').write_bytes(CONFIG.read_bytes())
            json_atomico(SAIDA/'ambiente.json',{'data_utc':agora(),**contrato['ambiente']})
            json_atomico(cp,contrato)
        cfg_path=SAIDA/'config.cfg';digest=sha(cp);rows=[]
        for n,t in enumerate(p['tarefas'],1):
            conferir_prazo(prazo)
            d=SAIDA/'execucoes'/f"{t['instancia']}__{t['metodo']}__{t['semente']}"
            if d.exists():
                conferir(d,t,cfg_path,cfg,60,digest)
            else:
                exigir(not somente_analisar,f'Resultado ausente: {d}')
                pend=SAIDA/'.pendentes';pend.mkdir(exist_ok=True)
                temp=Path(tempfile.mkdtemp(prefix=d.name+'__',dir=pend))
                comando=[str(RAIZ/'bin/tp3'),'--instancia',t['caminho_instancia'],'--metodo',t['metodo'],
                    '--config',str(cfg_path),'--semente',str(t['semente']),'--cpu','60','--saida',str(temp),'--salvar-solucao']
                print(f"[{n}/108] {t['instancia']} {t['metodo']} semente {t['semente']}",flush=True)
                inicio=agora()
                with (temp/'stdout.txt').open('w') as out,(temp/'stderr.txt').open('w') as err:
                    exigir(processo(comando,fd,out,err)==0,f'Falha; logs em {temp}')
                exigir(sha(CONFIG)==p['config_sha256']==sha(cfg_path) and
                    sha(RAIZ/'bin/tp3')==contrato['ambiente']['executavel_sha256'],'Configuração/executável alterado.')
                exigir(sha(Path(t['caminho_instancia']))==t['sha256_instancia'],'Instância alterada.')
                resultado,solucao=validar(temp,Path(t['caminho_instancia']),esperado(t,cfg_path,60),cfg)
                json_atomico(temp/'concluida.json',dict(versao=1,tarefa=t,contrato_sha256=digest,
                    inicio_utc=inicio,fim_utc=agora(),codigo_saida=0,comando=comando,
                    arquivos={f.name:sha(f) for f in [resultado,solucao]}))
                d.parent.mkdir(parents=True,exist_ok=True);temp.rename(d)
            rows.append(linha_csv(next(f for f in d.glob('*.csv') if not f.name.endswith('.solucao.csv'))))
            print(barra_progresso(n,108),flush=True)
        exigir(len(list((SAIDA/'execucoes').iterdir()))==108,'Execuções excedentes.')
        conferir_prazo(prazo)
        gravar_tabela(SAIDA/'tabela_comparacao.csv',rows,METODOS,{t['instancia'] for t in p['tarefas']},SEMENTES)
        json_atomico(SAIDA/'integridade.json',dict(valido=True,execucoes=108,contrato_sha256=digest,
            uso=p['uso'],familias=dict(Counter(t['familia'] for t in p['tarefas']))))
        print(f'Benchmark reduzido completo: 108 soluções validadas. Tabela: {SAIDA / "tabela_comparacao.csv"}')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-minutos',type=float,default=120,help='Teto total de parede; padrão 120 minutos.')
    g=parser.add_mutually_exclusive_group();g.add_argument('--planejar',action='store_true');g.add_argument('--analisar',action='store_true')
    a=parser.parse_args()
    if not math.isfinite(a.max_minutos) or a.max_minutos<=0:parser.error('Teto deve ser positivo e finito.')
    prazo=time.monotonic()+60*a.max_minutos
    def expirar(signum,frame):
        raise TimeoutError('Teto total atingido; resultados completos preservados. Repita o comando para retomar.')
    anterior=signal.signal(signal.SIGALRM,expirar)
    signal.setitimer(signal.ITIMER_REAL,60*a.max_minutos)
    try:
        p=plano()
        if a.planejar:
            print('108 execuções: 6 instâncias finais × 6 métodos × 3 sementes × até 60 s CPU.')
            print('Instâncias:',', '.join(dict.fromkeys(t['instancia'] for t in p['tarefas'])))
            return 0
        executar(p,prazo,a.analisar)
    except TimeoutError as e:print(str(e),file=sys.stderr);return 124
    except KeyboardInterrupt:print('Interrompido; repita o comando para retomar.',file=sys.stderr);return 130
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as e:
        print(f'Erro: {e}. Resultados completos preservados.',file=sys.stderr);return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,anterior)
    return 0


if __name__=='__main__':sys.exit(main())
