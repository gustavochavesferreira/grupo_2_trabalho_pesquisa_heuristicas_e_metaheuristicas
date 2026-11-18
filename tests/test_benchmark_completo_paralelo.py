from collections import Counter
import csv
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import benchmark_completo_paralelo as bc
import benchmark_reduzido_paralelo as par
import piloto_paralelo as pp

CPUS_TESTE = sorted(os.sched_getaffinity(0))
NUCLEOS = [CPUS_TESTE[k % len(CPUS_TESTE)] for k in range(6)]
FIXTURE = bc.RAIZ/'tests/data/integracao/limite_inicial.txt'


def aponta_fixture(tarefas, raiz):
    for t in tarefas:
        origem = raiz/(t['instancia']+'.ins2D')
        origem.write_bytes(FIXTURE.read_bytes())
        t['caminho_instancia'] = str(origem); t['sha256_instancia'] = bc.sha(origem)


class BenchmarkCompletoParalelo(unittest.TestCase):
    def setUp(self):
        fixar = patch.object(par, 'nucleos_fisicos', return_value=NUCLEOS)
        fixar.start()
        self.addCleanup(fixar.stop)

    def piloto_fixture(self, raiz, inicial):
        saida = raiz/'piloto'/inicial
        p = pp.plano(6, 3, 1, inicial)
        aponta_fixture(p['tarefas'], raiz)
        par.executar(p, None, False, saida, 6)
        return saida

    def test_selecao_audita_piloto_e_inicial(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            for inicial in bc.INICIAIS:
                lote = self.piloto_fixture(raiz, inicial)
                selo = bc.selecionar_h_estrela(lote, inicial, sementes=[1001])
                self.assertIn(selo['H_estrela'], bc.PROPOSTAS)
                self.assertEqual((selo['inicial'], selo['execucoes_validas']), (inicial, 40))
                self.assertEqual(selo['piloto_contrato_sha256'], bc.sha(lote/'contrato.json'))
                # Lote de uma inicial não serve para selecionar H* da outra.
                outra = next(i for i in bc.INICIAIS if i != inicial)
                with self.assertRaises(ValueError):
                    bc.selecionar_h_estrela(lote, outra, sementes=[1001])
            # Recibo adulterado (comando sem --inicial) é recusado.
            lote = raiz/'piloto/aleatoria'
            recibo = next(lote.glob('execucoes/*/concluida.json'))
            dados = json.loads(recibo.read_text()); dados['comando'] = dados['comando'][:-2]
            recibo.write_text(json.dumps(dados))
            with self.assertRaises(ValueError):
                bc.selecionar_h_estrela(lote, 'aleatoria', sementes=[1001])

    def test_plano_matriz_final_e_argumentos_por_tarefa(self):
        for inicial in bc.INICIAIS:
            p = bc.plano(6, 42, {'inicial': inicial, 'H_estrela': 'Hbase'}, inicial)
            self.assertEqual(len(p['tarefas']), 9180)
            self.assertEqual(dict(Counter(t['familia'] for t in p['tarefas'])), bc.FAMILIAS)
            self.assertEqual(p['metodos'], ['Hbase', 'Hext', 'Hint', 'Hcomb', 'Haleat', 'RLS-f7'])
            for t in p['tarefas']:
                esperado = [] if t['metodo'] == 'RLS-f7' or inicial == 'gulosa' else ['--inicial', 'aleatoria']
                self.assertEqual(t['args_extras'], esperado)
            with self.assertRaises(ValueError):
                bc.plano(6, 42, {'inicial': 'gulosa' if inicial == 'aleatoria' else 'aleatoria'}, inicial)

    def test_execucao_mista_rls_sem_inicial_e_comparacoes(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp); saida = raiz/'final'
            p = bc.plano(6, 5, {'inicial': 'aleatoria', 'H_estrela': 'Hbase'}, 'aleatoria')
            ids = list(dict.fromkeys(t['instancia'] for t in p['tarefas']))[:2]
            p['tarefas'] = [t for t in p['tarefas'] if t['instancia'] in ids and t['semente'] == 1001]
            p['sementes'] = [1001]
            p['paralelismo']['ordem_execucao'] = par.ordem(p['tarefas'], 5)
            aponta_fixture(p['tarefas'], raiz)
            par.executar(p, None, False, saida, 6)
            recibos = [json.loads(f.read_text()) for f in saida.glob('execucoes/*/concluida.json')]
            self.assertEqual(len(recibos), 12)
            for r in recibos:
                tem = r['comando'][-2:] == ['--inicial', 'aleatoria']
                self.assertEqual(tem, r['tarefa']['metodo'] != 'RLS-f7')
            linhas = bc.comparar_h_estrela(saida, p)
            self.assertEqual([c['outro'] for c in linhas], ['Hext', 'Hint', 'Hcomb', 'Haleat', 'RLS-f7'])
            self.assertTrue(all(c['vitorias_H']+c['empates']+c['derrotas_H'] == 2 for c in linhas))
            with (saida/'comparacoes_h_estrela.csv').open() as f:
                self.assertEqual(len(list(csv.DictReader(f))), 5)

    def test_p_sinais(self):
        self.assertEqual(bc.p_sinais(0, 0), 1.0)
        self.assertAlmostEqual(bc.p_sinais(1, 8), 0.0390625)
        self.assertAlmostEqual(bc.p_sinais(5, 5), 1.0)


if __name__ == '__main__':
    unittest.main()
