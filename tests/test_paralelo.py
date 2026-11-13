import csv
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import benchmark_paralelo as paralelo
from monitor_ram import MonitorRam,memoria_arvore


class Paralelo(unittest.TestCase):
    def test_interrupcao_encerra_filho_e_preserva_pendencia(self):
        p=paralelo.plano();p['tarefas']=p['tarefas'][:1]
        env=paralelo.ambiente();popen=paralelo.subprocess.Popen
        with tempfile.TemporaryDirectory() as tmp:
            lote=Path(tmp)/'lote'
            def lento(cmd,**kw):
                filho=popen([sys.executable,'-c','import time; time.sleep(30)'],**kw)
                (Path(kw['stdout'].name).parent/'pid.txt').write_text(str(filho.pid))
                return filho
            with patch.object(paralelo,'ambiente',return_value=env),patch.object(paralelo.subprocess,'Popen',side_effect=lento):
                with self.assertRaises(TimeoutError):
                    paralelo.executar(p,paralelo.nucleos_fisicos()[:1],lote,max_minutos=.005)
            self.assertFalse(list(lote.glob('execucoes/*/concluida.json')))
            pids=list(lote.glob('.pendentes/*/pid.txt'))
            self.assertEqual(len(pids),1)
            with self.assertRaises(ProcessLookupError):os.kill(int(pids[0].read_text()),0)
            self.assertTrue((lote/'ram.csv').exists())

    def test_monitor_arvore_e_janela(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp)
            for pid,rss,filhos in [(1,100,'2'),(2,200,'')]:
                d=raiz/str(pid);(d/'task'/str(pid)).mkdir(parents=True)
                (d/'status').write_text(f'VmRSS:\t{rss} kB\nVmSwap:\t5 kB\nCampoVazio:\n')
                (d/'task'/str(pid)/'children').write_text(filhos)
            (raiz/'meminfo').write_text('MemAvailable: 1000 kB\nSwapTotal: 500 kB\nSwapFree: 400 kB\n')
            self.assertEqual(memoria_arvore(1,raiz),(300,10,1000,100))
            m=MonitorRam(raiz/'ram.csv',intervalo=.02,amostra=.01)
            m.iniciar();time.sleep(.06);m.finalizar()
            with (raiz/'ram.csv').open() as f:rs=list(csv.DictReader(f))
            self.assertGreaterEqual(len(rs),2)
            self.assertTrue(all(float(r['pico_RSS_observado_sessao_MiB'])>=float(r['RSS_atual_MiB']) for r in rs))

    def test_execucao_paralela_real_e_retomada(self):
        cpus=paralelo.nucleos_fisicos()
        if len(cpus)<2:self.skipTest('Requer dois núcleos físicos disponíveis.')
        p=paralelo.plano()
        # Duas instâncias pequenas, seis métodos, uma semente, em arquivos temporários.
        ids=list(dict.fromkeys(t['instancia'] for t in p['tarefas']))[:2]
        p['tarefas']=[t for t in p['tarefas'] if t['instancia'] in ids and t['semente']==1001]
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp)
            for t in p['tarefas']:
                origem=raiz/(t['instancia']+'.ins2D')
                origem.write_bytes((paralelo.RAIZ/'tests/data/integracao/limite_inicial.txt').read_bytes())
                t['caminho_instancia']=str(origem);t['sha256_instancia']=paralelo.sha(origem)
            lote=raiz/'lote'
            paralelo.executar(p,cpus[:2],lote)
            recibos=list(lote.glob('execucoes/*/concluida.json'))
            self.assertEqual(len(recibos),12)
            registros=[json.loads(f.read_text()) for f in recibos]
            self.assertEqual({r['cpu_logica'] for r in registros},set(cpus[:2]))
            por_instancia={}
            for r in registros:por_instancia.setdefault(r['tarefa']['instancia'],set()).add(r['cpu_logica'])
            self.assertTrue(all(len(v)==1 for v in por_instancia.values()))
            antes={str(f):f.read_bytes() for f in recibos}
            paralelo.executar(p,cpus[:2],lote,analisar=True)
            self.assertTrue(all(Path(f).read_bytes()==v for f,v in antes.items()))
            self.assertTrue((lote/'ram.csv').is_file())
            with (lote/'tabela_comparacao.csv').open() as f:self.assertEqual(len(list(csv.DictReader(f))),6)


if __name__=='__main__':unittest.main()
