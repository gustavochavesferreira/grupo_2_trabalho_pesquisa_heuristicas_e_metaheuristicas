"""Módulo paralelo exploratório: uma instância por núcleo físico, sem alterar o sequencial."""

import argparse
from collections import defaultdict
import json
import multiprocessing as mp
import os
from pathlib import Path
from queue import Empty
import signal
import subprocess
import sys
import tempfile
import time

from benchmark_reduzido import plano as plano_reduzido, CONFIG
from executar_experimentos import (RAIZ,METODOS,SEMENTES,agora,ambiente,configuracao,
    conferir,exclusividade,esperado,json_atomico,ler_manifesto,sha)
from monitor_ram import MonitorRam
from piloto import barra_progresso
from tabela_comparacao import gravar_tabela
from validar_execucao import exigir,linha_csv,validar
from verificar_congelamento import verificar


def nucleos_fisicos():
    selecionados={}
    for cpu in sorted(os.sched_getaffinity(0)):
        top=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        try:chave=((top/'physical_package_id').read_text().strip(),(top/'core_id').read_text().strip())
        except OSError:chave=('cpu',str(cpu))
        selecionados.setdefault(chave,cpu)
    return list(selecionados.values())


def plano(completo=False):
    p=plano_reduzido()
    if completo:
        tarefas=[]
        for r in ler_manifesto(RAIZ/'instances/manifests/final.csv'):
            origem=(RAIZ/'instances/source'/r['caminho']).resolve()
            exigir(origem.is_relative_to((RAIZ/'instances/source').resolve()) and sha(origem)==r['sha256'],'Instância alterada.')
            for m in METODOS:
                for s in SEMENTES:
                    tarefas.append(dict(instancia=r['identificador'],familia=r['familia'],metodo=m,semente=s,caminho_instancia=str(origem),sha256_instancia=r['sha256']))
        p['tarefas']=tarefas
    p['uso']='exploratorio_paralelo_nao_integra_benchmark_sequencial_TP3'
    p['executor_sha256']=sha(Path(__file__))
    p['monitor_sha256']=sha(RAIZ/'scripts/monitor_ram.py')
    return p


def rodar_tarefa(t,lote,cfg,digest,env,fd,parar,cpu):
    d=lote/'execucoes'/f"{t['instancia']}__{t['metodo']}__{t['semente']}"
    cfg_path=lote/'config.cfg'
    if d.exists():
        conferir(d,t,cfg_path,cfg,60,digest)
        return
    pend=lote/'.pendentes';pend.mkdir(exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix=d.name+'__',dir=pend))
    cmd=[str(RAIZ/'bin/tp3'),'--instancia',t['caminho_instancia'],'--metodo',t['metodo'],'--config',str(cfg_path),'--semente',str(t['semente']),'--cpu','60','--saida',str(temp),'--salvar-solucao']
    inicio=agora()
    with (temp/'stdout.txt').open('w') as out,(temp/'stderr.txt').open('w') as err:
        with subprocess.Popen(cmd,cwd=RAIZ,stdin=subprocess.DEVNULL,stdout=out,stderr=err,pass_fds=(fd,)) as filho:
            try:
                while True:
                    if parar.is_set():raise InterruptedError('Interrompido pelo controlador.')
                    try:codigo=filho.wait(timeout=.2);break
                    except subprocess.TimeoutExpired:pass
            finally:
                if filho.poll() is None:
                    filho.terminate()
                    try:filho.wait(timeout=5)
                    except subprocess.TimeoutExpired:filho.kill();filho.wait()
    exigir(codigo==0,f'Falha {codigo}; logs em {temp}')
    exigir(sha(CONFIG)==sha(cfg_path) and sha(RAIZ/'bin/tp3')==env['executavel_sha256'],'Configuração/executável alterado.')
    exigir(sha(Path(t['caminho_instancia']))==t['sha256_instancia'],'Instância alterada.')
    r,s=validar(temp,Path(t['caminho_instancia']),esperado(t,cfg_path,60),cfg)
    json_atomico(temp/'concluida.json',dict(versao=1,tarefa=t,contrato_sha256=digest,inicio_utc=inicio,
        fim_utc=agora(),codigo_saida=0,comando=cmd,cpu_logica=cpu,arquivos={f.name:sha(f) for f in [r,s]}))
    d.parent.mkdir(parents=True,exist_ok=True);temp.rename(d)


def trabalhador(fila,eventos,parar,cpu,lote,cfg,digest,env,fd):
    signal.signal(signal.SIGINT,signal.SIG_IGN)
    try:
        os.sched_setaffinity(0,{cpu})
        while not parar.is_set():
            grupo=fila.get()
            if grupo is None:return
            for t in grupo:
                if parar.is_set():return
                rodar_tarefa(t,lote,cfg,digest,env,fd,parar,cpu)
                eventos.put(('ok',t['instancia'],t['metodo'],t['semente']))
    except InterruptedError:pass
    except BaseException as e:
        eventos.put(('erro',str(e)));parar.set()


def executar(p,cpus,lote,max_minutos=None,analisar=False):
    ctx=mp.get_context('fork')
    with exclusividade(RAIZ/'results/.execucao.lock') as fd:
        env=ambiente();cfg=configuracao(CONFIG)
        contrato={**p,'ambiente':env,'cpus':cpus,'unidade_paralela':'instancia'}
        cp=lote/'contrato.json'
        if cp.exists():
            exigir(json.loads(cp.read_text())==contrato,'Contrato paralelo difere; use o mesmo código, ambiente e número de trabalhadores.')
            exigir(sha(lote/'config.cfg')==sha(CONFIG),'Configuração do lote alterada.')
        else:
            exigir(not analisar,'Lote ainda não executado.')
            exigir(not (lote/'execucoes').exists(),'Resultados sem contrato.')
            lote.mkdir(parents=True,exist_ok=True);(lote/'config.cfg').write_bytes(CONFIG.read_bytes())
            json_atomico(cp,contrato)
            json_atomico(lote/'ambiente.json',{'data_utc':agora(),**env})
        digest=sha(cp)
        if not analisar:
            grupos=defaultdict(list)
            for t in p['tarefas']:grupos[t['instancia']].append(t)
            fila=ctx.Queue();eventos=ctx.Queue();parar=ctx.Event()
            filhos=[ctx.Process(target=trabalhador,args=(fila,eventos,parar,cpu,lote,cfg,digest,env,fd)) for cpu in cpus]
            monitor=MonitorRam(lote/'ram.csv');iniciados=[]
            inicio=time.monotonic();feitos=0
            try:
                # Todos os forks ocorrem antes das threads de monitoramento/filas.
                for f in filhos:f.start();iniciados.append(f)
                monitor.iniciar()
                for grupo in grupos.values():fila.put(grupo)
                for _ in filhos:fila.put(None)
                while feitos<len(p['tarefas']):
                    exigir(all(f.exitcode in [None,0] for f in filhos),'Trabalhador encerrou anormalmente, possivelmente por falta de memória; confira logs e sistema.')
                    if max_minutos is not None and time.monotonic()-inicio>=60*max_minutos:
                        raise TimeoutError('Teto de parede atingido; repita o comando para retomar.')
                    if monitor.erro:raise RuntimeError(str(monitor.erro))
                    try:e=eventos.get(timeout=.5)
                    except Empty:
                        exigir(any(f.is_alive() for f in filhos),'Trabalhadores encerraram sem completar o lote.');continue
                    exigir(e[0]=='ok',e[1])
                    feitos+=1;print(barra_progresso(feitos,len(p['tarefas'])),*e[1:],flush=True)
            finally:
                parar.set()
                for f in iniciados:f.join(timeout=10)
                for f in iniciados:
                    if f.is_alive():f.terminate();f.join()
                monitor.finalizar()
                fila.cancel_join_thread();fila.close();eventos.close()
        rows=[]
        nomes={f"{t['instancia']}__{t['metodo']}__{t['semente']}" for t in p['tarefas']}
        exigir({d.name for d in (lote/'execucoes').iterdir()}==nomes,'Matriz ausente ou excedente.')
        for t in p['tarefas']:
            d=lote/'execucoes'/f"{t['instancia']}__{t['metodo']}__{t['semente']}"
            conferir(d,t,lote/'config.cfg',cfg,60,digest)
            rows.append(linha_csv(next(f for f in d.glob('*.csv') if not f.name.endswith('.solucao.csv'))))
        gravar_tabela(lote/'tabela_comparacao.csv',rows,METODOS,{t['instancia'] for t in p['tarefas']},sorted({t['semente'] for t in p['tarefas']}))
        json_atomico(lote/'integridade.json',dict(valido=True,execucoes=len(rows),uso=p['uso'],contrato_sha256=digest))
        print(f'Lote paralelo validado. Tabela e RAM: {lote}',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--completo',action='store_true',help='Usa 153 instâncias e dez sementes; execução exploratória paralela.')
    parser.add_argument('--trabalhadores',type=int,help='Padrão: um por núcleo físico disponível, limitado pelo número de instâncias.')
    parser.add_argument('--max-minutos',type=float)
    g=parser.add_mutually_exclusive_group();g.add_argument('--planejar',action='store_true');g.add_argument('--analisar',action='store_true')
    a=parser.parse_args()
    import math
    if a.max_minutos is not None and (not math.isfinite(a.max_minutos) or a.max_minutos<=0):parser.error('Teto inválido.')
    def interromper(signum,frame):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,interromper)
    try:
        p=plano(a.completo);disponiveis=nucleos_fisicos()
        n=a.trabalhadores if a.trabalhadores is not None else min(len(disponiveis),len({t['instancia'] for t in p['tarefas']}))
        exigir(1<=n<=len(disponiveis),'Trabalhadores devem caber nos núcleos físicos disponíveis.')
        cpus=disponiveis[:n]
        lote=RAIZ/'results/paralelo'/('completo' if a.completo else 'reduzido')/cfg_id()
        print(f'Paralelo exploratório: {len(p["tarefas"])} execuções; {n} trabalhadores; CPUs {cpus}.')
        if not a.planejar:executar(p,cpus,lote,a.max_minutos,a.analisar)
    except TimeoutError as e:print(str(e),file=sys.stderr);return 124
    except KeyboardInterrupt:print('Interrompido. Resultados completos preservados.',file=sys.stderr);return 130
    except (OSError,ValueError,KeyError,RuntimeError) as e:print(f'Erro: {e}',file=sys.stderr);return 1
    return 0


def cfg_id():return configuracao(CONFIG)['id']


if __name__=='__main__':sys.exit(main())
