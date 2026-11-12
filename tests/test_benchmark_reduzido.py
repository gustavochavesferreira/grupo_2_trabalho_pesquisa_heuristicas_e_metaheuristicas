import csv
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import benchmark_reduzido as reduzido
from tabela_comparacao import gravar_tabela


class BenchmarkReduzido(unittest.TestCase):
    def test_plano_sem_piloto_formal(self):
        p=reduzido.plano()
        self.assertEqual(len(p['tarefas']),108)
        self.assertEqual({t['instancia'] for t in p['tarefas']},
            {'A36','A32','BENG03','BENG05','cl_03_100_01','cl_07_100_01'})
        self.assertEqual(len({(t['instancia'],t['metodo'],t['semente']) for t in p['tarefas']}),108)

    def test_tabela_recusa_duplicatas_e_limites_diferentes(self):
        a=dict(instancia='i',metodo='a',semente='1',LBref='1',K='2',desvio='100',
               alcancou_lb='0',tempo_melhor='0.1',tempo_total='1',motivo_parada='orcamento_reparo')
        b={**a,'metodo':'b','LBref':'2'}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'t.csv'
            with self.assertRaises(ValueError):gravar_tabela(path,[a,a],['a','b'],['i'],[1])
            with self.assertRaises(ValueError):gravar_tabela(path,[a,b],['a','b'],['i'],[1])
            b['LBref']='1'
            self.assertEqual(len(gravar_tabela(path,[a,b],['a','b'],['i'],[1])),2)

    def test_execucao_validacao_retomada_em_fixtures_pequenas(self):
        p=reduzido.plano()
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp)
            for t in p['tarefas']:
                origem=raiz/(t['instancia']+'.ins2D')
                origem.write_bytes((reduzido.RAIZ/'tests/data/integracao/limite_inicial.txt').read_bytes())
                t['caminho_instancia']=str(origem);t['sha256_instancia']=reduzido.sha(origem)
            with patch.object(reduzido,'SAIDA',raiz/'resultados'):
                reduzido.executar(p,None,False)
                recibos={str(f):f.read_bytes() for f in (raiz/'resultados').glob('execucoes/*/concluida.json')}
                self.assertEqual(len(recibos),108)
                with patch.object(reduzido,'processo',side_effect=AssertionError('Retomada repetiu execução')):
                    reduzido.executar(p,None,True)
                self.assertTrue(all(Path(f).read_bytes()==v for f,v in recibos.items()))
                with (raiz/'resultados/tabela_comparacao.csv').open() as f:rs=list(csv.DictReader(f))
                self.assertEqual(len(rs),6)
                self.assertTrue(all(r['execucoes']=='18' for r in rs))


if __name__=='__main__':unittest.main()
