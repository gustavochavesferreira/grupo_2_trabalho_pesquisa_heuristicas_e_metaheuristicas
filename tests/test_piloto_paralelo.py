import csv
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import piloto_paralelo as pp
import benchmark_reduzido_paralelo as par

CPUS_TESTE = sorted(os.sched_getaffinity(0))
NUCLEOS = [CPUS_TESTE[k % len(CPUS_TESTE)] for k in range(6)]


class PilotoParalelo(unittest.TestCase):
    def setUp(self):
        fixar = patch.object(par, 'nucleos_fisicos', return_value=NUCLEOS)
        fixar.start()
        self.addCleanup(fixar.stop)

    def test_matriz_do_piloto_nas_duas_iniciais(self):
        ids = {r['identificador'] for r in csv.DictReader(open(pp.RAIZ/'instances/manifests/piloto.csv'))}
        for inicial, args in [('gulosa', []), ('aleatoria', ['--inicial', 'aleatoria'])]:
            p = pp.plano(6, 42, 10, inicial)
            self.assertEqual(len(p['tarefas']), 400)
            self.assertEqual({t['instancia'] for t in p['tarefas']}, ids)
            self.assertEqual(p['metodos'], ['Hbase', 'Hext', 'Hint', 'Hcomb'])
            self.assertEqual(p['sementes'], list(range(1001, 1011)))
            self.assertEqual(p['args_extras'], args)
        self.assertNotEqual(pp.saida_lote('gulosa', 10, 6), pp.saida_lote('aleatoria', 10, 6))

    def test_execucao_das_duas_iniciais_em_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            for inicial in pp.INICIAIS:
                saida = raiz/inicial
                p = pp.plano(6, 3, 1, inicial)
                for t in p['tarefas']:
                    origem = raiz/(t['instancia']+'.ins2D')
                    origem.write_bytes((pp.RAIZ/'tests/data/integracao/limite_inicial.txt').read_bytes())
                    t['caminho_instancia'] = str(origem); t['sha256_instancia'] = pp.sha(origem)
                par.executar(p, None, False, saida, 6)
                recibos = [json.loads(f.read_text()) for f in saida.glob('execucoes/*/concluida.json')]
                self.assertEqual(len(recibos), 40)
                self.assertTrue(all(r['comando'][len(r['comando'])-len(p['args_extras']):] == p['args_extras'] or not p['args_extras'] for r in recibos))
                with (saida/'tabela_comparacao.csv').open() as f:
                    self.assertEqual([r['metodo'] for r in csv.DictReader(f)], ['Hbase', 'Hext', 'Hint', 'Hcomb'])
                self.assertEqual(json.loads((saida/'integridade.json').read_text())['uso'],
                                 f'piloto_paralelo_exploratorio_sem_H_estrela_inicial_{inicial}')


if __name__ == '__main__':
    unittest.main()
