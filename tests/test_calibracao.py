import json
from pathlib import Path
import sys
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'scripts'))
from calibrar import criterio, gravar_imutavel, resumir, OPCOES
from executar_experimentos import configuracao, sha
from verificar_congelamento import verificar


class Calibracao(unittest.TestCase):
    def test_qualidade_antes_do_tempo(self):
        a = dict(id='a', desvio_medio=1, alcance_lb=0, tempo_melhor_mediano=5, cpu_media=5)
        b = dict(id='b', desvio_medio=2, alcance_lb=1, tempo_melhor_mediano=0, cpu_media=0)
        self.assertEqual(min([b, a], key=criterio)['id'], 'a')
        b['desvio_medio'] = 1
        self.assertEqual(min([a, b], key=criterio)['id'], 'b')
        a['alcance_lb'] = 1
        self.assertEqual(min([a, b], key=criterio)['id'], 'b')

    def test_grade_e_media_pareada(self):
        grade = [configuracao(RAIZ / f'config/calibracao/{o}.cfg') for o in OPCOES]
        self.assertEqual(len({g['id'] for g in grade}), 4)
        self.assertTrue(all(g['estado'] == 'provisorio' for g in grade))
        linhas = [dict(K='3', desvio='50', alcancou_lb='0', tempo_melhor='2', tempo_total='3'),
                  dict(K='2', desvio='0', alcancou_lb='1', tempo_melhor='1', tempo_total='2')]
        r = resumir('teste', linhas)
        self.assertEqual((r['desvio_medio'], r['alcance_lb'], r['tempo_melhor_mediano']), (25, .5, 1.5))

    def test_congelamento_sem_sobrescrita_e_selo(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); cfg = p/'c.cfg'; sementes = p/'sementes.txt'; selo = p/'c.json'
            gravar_imutavel(cfg, 'dados\n')
            gravar_imutavel(cfg, 'dados\n')
            with self.assertRaises(ValueError):
                gravar_imutavel(cfg, 'outros\n')
            sementes.write_text('1001\n')
            selo.write_text(json.dumps(dict(config_sha256=sha(cfg), sementes_sha256=sha(sementes), execucoes_validas=160, plano_sha256=sha(RAIZ / 'docs/calibracao.md'))))
            verificar(cfg, selo, sementes)
            cfg.chmod(0o644); cfg.write_text('editado')
            with self.assertRaises(ValueError):
                verificar(cfg, selo, sementes)


if __name__ == '__main__':
    unittest.main()
