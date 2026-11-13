import csv
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import benchmark_reduzido_paralelo as par
import benchmark_reduzido as base


def plano_fixture(raiz, jobs, semente):
    p = par.plano(jobs, semente)
    for t in p['tarefas']:
        origem = raiz/(t['instancia']+'.ins2D')
        origem.write_bytes((par.RAIZ/'tests/data/integracao/limite_inicial.txt').read_bytes())
        t['caminho_instancia'] = str(origem); t['sha256_instancia'] = par.sha(origem)
    return p


# Núcleos simulados com CPUs reais, para os testes não dependerem da topologia da máquina.
CPUS_TESTE = sorted(os.sched_getaffinity(0))
NUCLEOS = [CPUS_TESTE[k % len(CPUS_TESTE)] for k in range(6)]


class BenchmarkReduzidoParalelo(unittest.TestCase):
    def setUp(self):
        fixar = patch.object(par, 'nucleos_fisicos', return_value=NUCLEOS)
        fixar.start()
        self.addCleanup(fixar.stop)

    def test_plano_igual_ao_sequencial_e_ordem_reproduzivel(self):
        p = par.plano(6, 42)
        self.assertEqual(p['tarefas'], base.plano()['tarefas'])
        ordem = p['paralelismo']['ordem_execucao']
        self.assertEqual(ordem, par.plano(6, 42)['paralelismo']['ordem_execucao'])
        self.assertNotEqual(ordem, par.plano(6, 7)['paralelismo']['ordem_execucao'])
        self.assertEqual(sorted(ordem), sorted(par.nome(t) for t in p['tarefas']))
        self.assertEqual(par.plano(6, None)['paralelismo']['ordem_execucao'], [par.nome(t) for t in p['tarefas']])

    def test_execucao_paralela_validacao_retomada_e_contrato(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp); saida = raiz/'resultados'
            p = plano_fixture(raiz, 4, 3)
            par.executar(p, None, False, saida, 4)
            recibos = {str(f): f.read_bytes() for f in saida.glob('execucoes/*/concluida.json')}
            self.assertEqual(len(recibos), 108)
            with patch.object(par.Lote, 'rodar', side_effect=AssertionError('Retomada repetiu execução')):
                par.executar(p, None, True, saida, 4)
            self.assertTrue(all(Path(f).read_bytes() == v for f, v in recibos.items()))
            with (saida/'tabela_comparacao.csv').open() as f:
                rs = list(csv.DictReader(f))
            self.assertEqual(len(rs), 6)
            self.assertTrue(all(r['execucoes'] == '18' for r in rs))
            integ = json.loads((saida/'integridade.json').read_text())
            self.assertEqual(integ['paralelismo'], {'processos': 4, 'semente_ordem': 3, 'cpus': NUCLEOS[:4]})
            # Cada recibo registra a CPU em que a execução ficou fixada, dentre as do contrato.
            cpus = {json.loads(f.read_text())['cpu_logica'] for f in saida.glob('execucoes/*/concluida.json')}
            self.assertTrue(cpus <= set(NUCLEOS[:4]))
            # Outro -j no mesmo diretório é recusado.
            with self.assertRaises(ValueError):
                par.executar(plano_fixture(raiz, 2, 3), None, True, saida, 2)

    def test_jobs_acima_dos_nucleos_recusado(self):
        with self.assertRaises(ValueError):
            par.plano(7, None)

    def test_filho_fixado_no_nucleo(self):
        with tempfile.TemporaryDirectory() as tmp:
            lote = par.Lote.__new__(par.Lote)
            lote.fd = os.open(tmp, os.O_RDONLY); self.addCleanup(os.close, lote.fd)
            lote.parar = par.threading.Event(); lote.filhos = set(); lote.trava_filhos = par.threading.Lock()
            cpu = CPUS_TESTE[-1]
            # O filho espera um instante e escreve a própria afinidade.
            codigo = lote._executa_fixado([sys.executable, '-c', 'import os,time; time.sleep(0.2); print(sorted(os.sched_getaffinity(0)))'], Path(tmp), cpu)
            self.assertEqual(codigo, 0)
            self.assertEqual((Path(tmp)/'stdout.txt').read_text().strip(), str([cpu]))

    def test_resultado_corrompido_e_recusado(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp); saida = raiz/'resultados'
            p = plano_fixture(raiz, 6, None)
            par.executar(p, None, False, saida, 6)
            csv_res = next(f for f in (saida/'execucoes').glob('*/*.csv') if not f.name.endswith('.solucao.csv'))
            csv_res.write_text(csv_res.read_text().replace(',', ';', 1))
            with self.assertRaises(ValueError):
                par.executar(p, None, True, saida, 6)


if __name__ == '__main__':
    unittest.main()
