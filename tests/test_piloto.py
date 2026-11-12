from pathlib import Path
import sys
import tempfile
import unittest
import subprocess
import time
import json
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'scripts'))
import piloto


class Piloto(unittest.TestCase):
    def test_prazo_interrompe_filho_silencioso(self):
        inicio = time.monotonic()
        with self.assertRaises(TimeoutError):
            piloto.executar_com_progresso([sys.executable, '-c',
                'import time,signal; signal.signal(signal.SIGINT, lambda a,b: exit(130)); time.sleep(30)'], inicio+0.25)
        self.assertLess(time.monotonic()-inicio, 5)

    def test_prazo_vencido_nao_inicia_filho(self):
        with patch.object(piloto.subprocess, 'Popen') as popen:
            with self.assertRaises(TimeoutError):
                piloto.executar_com_progresso(['inexistente'], time.monotonic()-1)
            popen.assert_not_called()

    def test_plano_v2_sem_executar(self):
        p = subprocess.run([sys.executable, '-B', str(RAIZ/'scripts/piloto.py'), '--planejar'],
                           capture_output=True, text=True, check=True)
        dados = json.loads(p.stdout)
        self.assertEqual(dados['execucoes'], 400)
        self.assertEqual(dados['cpu'], 60)
        self.assertEqual(dados['config']['max_reinicios'], '50000')
        self.assertEqual(dados['config']['max_avaliacoes_reparo'], '1000000')

    def test_progresso_execucao_e_retomada(self):
        self.assertEqual(piloto.progresso_da_linha('[1/400] Executando: caso'), (0, 400))
        self.assertEqual(piloto.progresso_da_linha('[2/400] Executando: caso'), (1, 400))
        self.assertEqual(piloto.progresso_da_linha('[2/400] Válida, pulando: caso'), (2, 400))
        self.assertEqual(piloto.progresso_da_linha('Lote completo: 400 válidas; 400 puladas; 0 executadas.'), (400, 400))
        self.assertIsNone(piloto.progresso_da_linha('Erro: falha'))
        self.assertIn('200/400 (50.0%)', piloto.barra_progresso(200, 400))

    def test_criterios_e_precisao(self):
        a = dict(desvio_exato='1/3', alcances_lb=10, tempo_melhor_mediano=2)
        b = dict(desvio_exato='33333333333333334/100000000000000000', alcances_lb=100, tempo_melhor_mediano=0)
        self.assertLess(piloto.criterio(a), piloto.criterio(b))
        b['desvio_exato'] = '1/3'
        self.assertLess(piloto.criterio(b), piloto.criterio(a))
        b['alcances_lb'] = 10
        self.assertLess(piloto.criterio(b), piloto.criterio(a))

    def test_cem_resultados_por_metodo(self):
        linhas = [dict(K='3', LBref='2', alcancou_lb='0', tempo_melhor='1')] * 100
        r = piloto.resumir('Hbase', linhas)
        self.assertEqual((r['desvio_exato'], r['K_medio'], r['tempo_melhor_mediano']), ('50', 3, 1))
        with self.assertRaises(ValueError):
            piloto.resumir('Hbase', linhas[:99])

    def test_sem_matriz_nao_congela(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.object(piloto, 'RAIZ', Path(t)), patch.object(piloto, 'verificar'), patch.object(piloto, 'configuracao', return_value={'id':'congelada_v2'}):
                with self.assertRaises(FileNotFoundError):
                    piloto.analisar()
            self.assertFalse((Path(t)/'config/h_estrela_v2.json').exists())


if __name__ == '__main__':
    unittest.main()
