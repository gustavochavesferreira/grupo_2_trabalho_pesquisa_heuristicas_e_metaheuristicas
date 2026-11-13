"""Monitor Linux: RSS da árvore de processos, amostrado a cada segundo."""

import csv
import os
from pathlib import Path
import threading
import time
from executar_experimentos import agora


def memoria_arvore(pid, proc=Path('/proc')):
    pendentes=[pid]; vistos=set(); rss=swap=0
    while pendentes:
        atual=pendentes.pop()
        if atual in vistos:continue
        vistos.add(atual)
        try:
            status=(proc/str(atual)/'status').read_text()
            valores={l.split(':',1)[0]:l.split(':',1)[1].strip().split()[0] for l in status.splitlines() if l.startswith(('VmRSS:','VmSwap:'))}
            rss+=int(valores.get('VmRSS',0));swap+=int(valores.get('VmSwap',0))
            pendentes.extend(map(int,(proc/str(atual)/'task'/str(atual)/'children').read_text().split()))
        except (FileNotFoundError,ProcessLookupError):pass
    mem={l.split(':')[0]:int(l.split()[1]) for l in (proc/'meminfo').read_text().splitlines()}
    return rss,swap,mem.get('MemAvailable',0),mem.get('SwapTotal',0)-mem.get('SwapFree',0)


class MonitorRam:
    def __init__(self,path,intervalo=60,amostra=1):
        self.path=path;self.intervalo=intervalo;self.amostra=amostra
        self.parar=threading.Event();self.thread=None;self.erro=None

    def iniciar(self):
        self.thread=threading.Thread(target=self.executar,daemon=True);self.thread.start()

    def finalizar(self):
        self.parar.set()
        if self.thread:self.thread.join()
        if self.erro:raise RuntimeError(f'Falha no monitor de RAM: {self.erro}')

    def executar(self):
        try:
            inicio=ultimo=time.monotonic();pico=janela=0
            novo=not self.path.exists()
            with self.path.open('a',newline='') as f:
                w=csv.writer(f)
                if novo:w.writerow(['utc','sessao_s','RSS_atual_MiB','pico_RSS_observado_sessao_MiB','pico_RSS_observado_janela_MiB','swap_processos_MiB','RAM_disponivel_sistema_MiB','swap_sistema_MiB'])
                primeira=True
                while True:
                    rss,swap,disponivel,swap_sistema=memoria_arvore(os.getpid())
                    pico=max(pico,rss);janela=max(janela,rss);agora_t=time.monotonic()
                    if primeira or self.parar.is_set() or agora_t-ultimo>=self.intervalo:
                        w.writerow([agora(),round(agora_t-inicio,2),rss/1024,pico/1024,janela/1024,swap/1024,disponivel/1024,swap_sistema/1024]);f.flush()
                        print(f'[RAM {agora_t-inicio:.0f}s] atual {rss/1024:.1f} MiB | pico observado {pico/1024:.1f} MiB | disponível {disponivel/1024:.0f} MiB | swap processos {swap/1024:.1f} MiB',flush=True)
                        ultimo=agora_t;janela=0;primeira=False
                    if self.parar.is_set():break
                    self.parar.wait(self.amostra)
        except Exception as e:self.erro=e
