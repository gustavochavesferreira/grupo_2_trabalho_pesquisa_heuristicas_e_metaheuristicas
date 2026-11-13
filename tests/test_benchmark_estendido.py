import csv
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import benchmark_estendido as est
import benchmark_reduzido_paralelo as par

IDS = ['A4', 'A10', 'A28', 'A32', 'A18', 'A9', 'BENG01', 'BENG02', 'BENG04', 'BENG08', 'BENG09', 'BENG10',
       'cl_01_020_01', 'cl_03_020_01', 'cl_05_060_01', 'cl_07_060_01', 'cl_08_100_01', 'cl_10_100_01']


# Núcleos simulados com CPUs reais, para os testes não dependerem da topologia da máquina.
CPUS_TESTE = sorted(os.sched_getaffinity(0))
NUCLEOS = [CPUS_TESTE[k % len(CPUS_TESTE)] for k in range(6)]


class BenchmarkEstendido(unittest.TestCase):
    def setUp(self):
        fixar = patch.object(par, 'nucleos_fisicos', return_value=NUCLEOS)
        fixar.start()
        self.addCleanup(fixar.stop)

    def test_plano_lista_sementes_e_ordem(self):
        p = est.plano(6, 42, 3)
        self.assertEqual(p['lista'], IDS)
        self.assertEqual(p['sementes'], [1001, 1002, 1003])
        self.assertEqual(len(p['tarefas']), 18*6*3)
        self.assertEqual(len({par.nome(t) for t in p['tarefas']}), 324)
        self.assertEqual(sorted(p['paralelismo']['ordem_execucao']), sorted(par.nome(t) for t in p['tarefas']))
        self.assertEqual(len(est.plano(6, None, 10)['tarefas']), 18*6*10)

    def test_lista_invalida_recusada(self):
        with tempfile.TemporaryDirectory() as tmp:
            for conteudo in ['A4\nA4\n', 'A14\n', 'XYZ\n', '# vazia\n']:
                lista = Path(tmp)/'l.txt'; lista.write_text(conteudo)
                with self.assertRaises(ValueError):
                    est.plano(6, None, 3, lista)

    def test_execucao_retomada_tabela_e_integridade(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp); saida = raiz/'resultados'
            p = est.plano(6, 7, 1)
            for t in p['tarefas']:
                origem = raiz/(t['instancia']+'.ins2D')
                origem.write_bytes((est.RAIZ/'tests/data/integracao/limite_inicial.txt').read_bytes())
                t['caminho_instancia'] = str(origem); t['sha256_instancia'] = est.sha(origem)
            par.executar(p, None, False, saida, 6)
            self.assertEqual(len(list((saida/'execucoes').iterdir())), 108)
            with patch.object(par.Lote, 'rodar', side_effect=AssertionError('Retomada repetiu execução')):
                par.executar(p, None, True, saida, 6)
            with (saida/'tabela_comparacao.csv').open() as f:
                rs = list(csv.DictReader(f))
            self.assertEqual(len(rs), 6)
            self.assertTrue(all(r['instancias'] == '18' and r['execucoes'] == '18' for r in rs))
            integ = json.loads((saida/'integridade.json').read_text())
            self.assertEqual((integ['execucoes'], integ['uso']), (108, 'benchmark_estendido_TA_sem_H_estrela'))


if __name__ == '__main__':
    unittest.main()
