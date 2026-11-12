import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import piloto_v1 as v1


class PilotoV1(unittest.TestCase):
    def test_expansao_preserva_contrato_original(self):
        a=v1.plano()
        b=v1.plano(v1.EXTRAS,v1.RAIZ/'results/ta_v1_extra')
        self.assertEqual(len(a['tarefas']),36)
        self.assertEqual(len(b['tarefas']),24)
        def chaves(p):
            return {(t['instancia'],t['metodo'],t['semente']) for t in p['tarefas']}
        self.assertFalse(chaves(a)&chaves(b))
        self.assertEqual(len(chaves(a)|chaves(b)),60)
        self.assertEqual(a['config'],b['config'])
        self.assertEqual((a['cpu'],b['cpu']),(60,60))


if __name__=='__main__':
    unittest.main()
