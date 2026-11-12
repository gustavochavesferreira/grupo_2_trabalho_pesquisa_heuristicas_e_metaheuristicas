"""Testa a interface real e lê seus CSVs com o parser independente do Python."""

import csv
from pathlib import Path
import subprocess
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
EXE = RAIZ / 'bin/tp3'


class TesteCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='tp3_cli_')
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.config = self.raiz / 'teste.cfg'
        self.texto_config = (RAIZ / 'config/provisoria.cfg').read_text().replace('100000000', '40')
        self.config.write_text(self.texto_config)

    def comando(self, metodo='Hbase', instancia=None, saida=None, semente=1001):
        return [str(EXE), '--instancia', str(instancia or RAIZ / 'tests/data/valida.txt'),
                '--metodo', metodo, '--config', str(self.config), '--semente', str(semente),
                '--cpu', '2', '--saida', str(saida or self.raiz / 'saida')]

    def rodar(self, comando, codigo=0):
        p = subprocess.run(comando, cwd=RAIZ, text=True, capture_output=True, timeout=15)
        self.assertEqual(p.returncode, codigo, p.stdout + p.stderr)
        return p

    def registro(self, pasta):
        arquivos = [p for p in pasta.glob('*.csv') if not p.name.endswith('.solucao.csv')]
        self.assertEqual(len(arquivos), 1)
        with arquivos[0].open(newline='') as f:
            leitor = csv.DictReader(f)
            self.assertEqual(len(leitor.fieldnames), len(set(leitor.fieldnames)))
            linhas = list(leitor)
        self.assertEqual(len(linhas), 1)
        self.assertNotIn(None, linhas[0])
        self.assertNotIn(None, linhas[0].values())
        return arquivos[0], linhas[0]

    def test_ajuda_e_erros_de_argumentos(self):
        self.assertIn('--instancia', self.rodar([str(EXE), '--ajuda']).stdout)
        self.assertIn('Controle auxiliar: Haleat', self.rodar([str(EXE)]).stdout)
        for args in [['--metodo', 'inventado'], ['--cpu', 'nan'], ['--semente', '-1'],
                     ['--semente', '4294967296'], ['--cpu', '0'], ['--desconhecida'],
                     ['--saida'], ['--salvar-solucao', '--salvar-solucao']]:
            comando = self.comando()
            if len(args) == 2 and args[0] in ['--metodo', '--cpu', '--semente']:
                comando[comando.index(args[0])+1] = args[1]
            else:
                comando += args
            p = self.rodar(comando, 1)
            self.assertIn('Erro:', p.stderr)
        self.assertFalse((self.raiz / 'saida').exists())

    def test_configuracao_estrita(self):
        casos = [self.texto_config + 'max_reinicios=9\n',
                 self.texto_config + 'chave_errada=1\n',
                 self.texto_config.replace('max_reinicios=5\n', ''),
                 self.texto_config.replace('versao=1', 'versao=2'),
                 self.texto_config.replace('estado=provisorio', 'estado=inventado'),
                 self.texto_config.replace('chapas_perturbadas=2', 'chapas_perturbadas=1'),
                 self.texto_config.replace('max_reinicios=5', 'max_reinicios=-1'),
                 self.texto_config.replace('max_reinicios=5', 'max_reinicios=1x'),
                 self.texto_config.replace('rls_max_avaliacoes=40', 'rls_max_avaliacoes=0'),
                 self.texto_config.replace('rls_max_avaliacoes=40', 'rls_max_avaliacoes=100000001'),
                 self.texto_config.replace('id=provisoria_v1', 'id=../fora'),
                 self.texto_config + 'linha sem igual\n']
        for texto in casos:
            self.config.write_text(texto)
            self.assertIn('Erro:', self.rodar(self.comando(), 1).stderr)
        self.assertFalse((self.raiz / 'saida').exists())

    def test_csv_solucao_escape_e_preservacao(self):
        instancia = self.raiz / 'instância,"com espaço".txt'
        instancia.write_bytes((RAIZ / 'tests/data/valida.txt').read_bytes())
        cmd = self.comando(instancia=instancia) + ['--salvar-solucao']
        self.rodar(cmd)
        arquivo, r = self.registro(self.raiz / 'saida')
        self.assertEqual(r['versao'], '1')
        self.assertEqual(r['caminho_instancia'], str(instancia))
        self.assertEqual(r['instancia'], instancia.stem)
        self.assertEqual(r['familia'], 'OUTRA')
        self.assertEqual(r['config_estado'], 'provisorio')
        self.assertEqual(r['chapas_perturbadas'], '2')
        self.assertEqual(r['max_reinicios'], '5')
        self.assertEqual(r['rls_max_avaliacoes'], '40')
        self.assertEqual(r['validada'], '1')
        self.assertEqual(r['metodo'], 'Hbase')
        self.assertEqual(r['controle_auxiliar'], '0')
        self.assertEqual(r['unidade_avaliacoes'], 'candidato_externo')
        self.assertEqual(r['f7'], '')
        self.assertEqual(r['ativacoes_internas'], '')
        self.assertEqual(r['historico_atualizacoes'], '')
        self.assertAlmostEqual(float(r['desvio']), 100*(int(r['K'])-int(r['LBref']))/int(r['LBref']))
        self.assertLessEqual(float(r['tempo_melhor']), float(r['tempo_total']))
        for t in ['0_1', '1', '5', '10', '30', '60']:
            self.assertGreaterEqual(int(r['K_'+t]), int(r['K']))
        solucao = arquivo.parent / r['solucao_arquivo']
        with solucao.open(newline='') as f:
            pecas = list(csv.DictReader(f))
        self.assertEqual(len(pecas), 6)
        self.assertEqual(len({p['copia_id'] for p in pecas}), 6)
        antes = {p.name: p.read_bytes() for p in arquivo.parent.iterdir()}
        self.assertIn('já existe', self.rodar(cmd, 1).stderr)
        self.assertEqual(antes, {p.name: p.read_bytes() for p in arquivo.parent.iterdir()})

    def test_rls_formato_e_f7_inteiro(self):
        instancia = self.raiz / 'grande.txt'
        instancia.write_text('2\n3000000000 3000000000\n1 3000000000 1 2 0 0\n2 1 3000000000 2 0 0\n')
        self.config.write_text(self.texto_config.replace('rls_max_avaliacoes=40', 'rls_max_avaliacoes=1'))
        encontrou_grande = False
        for semente in range(1001, 1101):
            saida = self.raiz / str(semente)
            self.rodar(self.comando('RLS-f7', instancia, saida, semente))
            _, r = self.registro(saida)
            f7 = int(r['f7'])
            self.assertEqual(f7, 9000000000000000000*(int(r['K'])-1)+int(r['area_perfil']))
            self.assertEqual(r['avaliacoes'], '1')
            self.assertEqual(r['unidade_avaliacoes'], 'f7')
            self.assertEqual(r['solucao_arquivo'], '')
            self.assertEqual(r['tentativas_reducao'], '')
            self.assertEqual(r['validada'], '1')
            if f7 > 2**64-1:
                encontrou_grande = True
                break
        self.assertTrue(encontrou_grande, 'O teste não exercitou f7 acima de 64 bits.')

    def test_erros_de_arquivos_e_cpu_sem_inicial(self):
        self.assertIn('Erro:', self.rodar(self.comando(instancia=self.raiz / 'ausente'), 1).stderr)
        self.assertIn('Erro:', self.rodar(self.comando(instancia=RAIZ / 'tests/data/demanda_zero.txt'), 1).stderr)
        bloqueado = self.raiz / 'arquivo'
        bloqueado.write_text('preservar')
        self.rodar(self.comando(saida=bloqueado), 1)
        self.assertEqual(bloqueado.read_text(), 'preservar')
        cmd = self.comando()
        cmd[cmd.index('--cpu')+1] = '1e-300'
        self.assertIn('primeira solução completa', self.rodar(cmd, 3).stderr)
        self.assertFalse((self.raiz / 'saida').exists())


if __name__ == '__main__':
    unittest.main()
