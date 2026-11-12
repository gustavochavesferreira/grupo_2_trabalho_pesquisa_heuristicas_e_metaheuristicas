"""Testa planejamento, publicação, retomada e exclusividade com saídas temporárias."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'scripts'))
import executar_experimentos as runner


class Orquestracao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='tp3_orquestracao_')
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.config = self.raiz / 'teste.cfg'
        self.texto = (RAIZ / 'config/provisoria.cfg').read_text().replace('id=provisoria_v1', 'id=teste20').replace('max_avaliacoes_reparo=1000', 'max_avaliacoes_reparo=0')
        self.config.write_text(self.texto)
        self.cmd = [sys.executable, str(RAIZ / 'scripts/executar_experimentos.py'), '--modo', 'calibration',
                    '--config', str(self.config), '--saida', str(self.raiz), '--instancias', 'A42',
                    '--metodos', 'Hbase', 'Hext', '--sementes', '1001', '1002', '--cpu', '2']
        self.lote = self.raiz / 'calibration/teste20'

    def rodar(self, cmd=None, codigo=0):
        r = subprocess.run(cmd or self.cmd, cwd=RAIZ, text=True, capture_output=True, timeout=60)
        self.assertEqual(r.returncode, codigo, r.stdout+r.stderr)
        return r

    def test_retomada_corrupcao_e_preservacao(self):
        self.rodar()
        pastas = sorted((self.lote / 'execucoes').iterdir())
        self.assertEqual(len(pastas), 4)
        antes = {p.name: (p / 'concluida.json').read_bytes() for p in pastas}
        self.assertIn('4 puladas; 0 executadas', self.rodar().stdout)
        (self.lote / '.pendentes/interrompida').mkdir()
        (self.lote / '.pendentes/interrompida/parcial.csv').write_text('incompleto')
        alvo = next(pastas[0].glob('*.csv'))
        alvo.write_text('CSV truncado\n')
        self.assertIn('3 puladas; 1 executadas', self.rodar().stdout)
        self.assertEqual(len(list((self.lote / 'invalidos').iterdir())), 1)
        for p in pastas[1:]:
            self.assertEqual(antes[p.name], (p / 'concluida.json').read_bytes())
        self.assertTrue((self.lote / '.pendentes/interrompida/parcial.csv').exists())
        # Mesmo alterando o checksum, uma solução geometricamente inválida não passa.
        p = pastas[0]
        solucao = next(p.glob('*.solucao.csv'))
        linhas = solucao.read_text().splitlines()
        campos = linhas[1].split(','); campos[4] = '999999999999'; linhas[1] = ','.join(campos)
        solucao.write_text('\n'.join(linhas)+'\n')
        recibo_path = p / 'concluida.json'
        recibo = json.loads(recibo_path.read_text())
        recibo['arquivos'][solucao.name] = runner.sha(solucao)
        recibo_path.write_text(json.dumps(recibo))
        self.assertIn('3 puladas; 1 executadas', self.rodar().stdout)
        self.assertEqual(len(list((self.lote / 'invalidos').iterdir())), 2)
        self.assertIn('4 puladas; 0 executadas', self.rodar().stdout)
        env = json.loads((self.lote / 'ambiente.json').read_text())
        for chave in ['compilador', 'build', 'kernel', 'cpu', 'ram', 'data_utc', 'executavel_sha256', 'fontes_sha256']:
            self.assertTrue(env[chave])

    def test_protocolo_alterado_nao_sobrescreve(self):
        self.rodar()
        antes = (self.lote / 'contrato.json').read_bytes()
        self.config.write_text(self.texto.replace('max_reinicios=5', 'max_reinicios=6'))
        self.assertIn('outro protocolo', self.rodar(codigo=1).stderr)
        self.assertEqual(antes, (self.lote / 'contrato.json').read_bytes())

    def test_planejamento_modos_e_sementes(self):
        def plano(modo, extras=(), codigo=0):
            cmd = self.cmd[:2] + ['--modo', modo, '--config', str(self.config), '--planejar'] + list(extras)
            return self.rodar(cmd, codigo)
        self.assertEqual(json.loads(plano('calibration').stdout)['execucoes'], 40)
        plano('pilot', codigo=1)
        self.config.write_text(self.texto.replace('estado=provisorio', 'estado=congelado'))
        for modo, n in [('pilot', 400), ('preflight', 918), ('final', 9180)]:
            dados = json.loads(plano(modo).stdout)
            self.assertEqual(dados['execucoes'], n)
            self.assertEqual(dados['cpu'], 60 if modo != 'preflight' else 1)
        plano('pilot', ['--cpu', '1'], codigo=1)
        plano('calibration', ['--metodos', 'RLS-f7'], codigo=1)
        plano('calibration', ['--sementes', '999'], codigo=1)
        plano('calibration', ['--instancias', 'BENG01'], codigo=1)
        self.assertEqual((RAIZ / 'config/sementes.txt').read_text().split(), list(map(str, range(1001, 1011))))

    def test_trava_global_e_heranca(self):
        with runner.exclusividade(RAIZ / 'results/.execucao.lock'):
            self.assertIn('trava global', self.rodar(codigo=1).stderr)
        trava = self.raiz / 'lock'
        with runner.exclusividade(trava) as fd:
            filho = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(0.3)'], pass_fds=(fd,))
        try:
            with self.assertRaises(ValueError):
                with runner.exclusividade(trava):
                    pass
        finally:
            filho.wait()
        with runner.exclusividade(trava):
            pass

    def test_interrupcao_finaliza_filho(self):
        filho = MagicMock()
        filho.__enter__.return_value = filho
        filho.wait.side_effect = [KeyboardInterrupt, 0]
        with patch.object(runner.subprocess, 'Popen', return_value=filho):
            with self.assertRaises(KeyboardInterrupt):
                runner.processo(['teste'], 1, None, None)
        filho.terminate.assert_called_once()
        self.assertEqual(filho.wait.call_count, 2)

    def test_validador_seis_metodos(self):
        instancia = RAIZ / 'tests/data/integracao/limite_inicial.txt'
        config = runner.configuracao(self.config)
        for metodo in runner.METODOS:
            pasta = self.raiz / metodo
            cmd = [str(RAIZ / 'bin/tp3'), '--instancia', str(instancia), '--metodo', metodo,
                   '--config', str(self.config), '--semente', '1001', '--cpu', '2',
                   '--saida', str(pasta), '--salvar-solucao']
            self.rodar(cmd)
            esperado = {'instancia': instancia.stem, 'familia': 'OUTRA', 'caminho_instancia': str(instancia),
                        'metodo': metodo, 'semente': 1001, 'config_arquivo': str(self.config), 'limite_cpu': '2'}
            csv, solucao = runner.validar(pasta, instancia, esperado, config)
            self.assertTrue(csv.is_file() and solucao.is_file())

    def test_esquema_e_marcos_corrompidos(self):
        instancia = RAIZ / 'tests/data/integracao/limite_inicial.txt'
        pasta = self.raiz / 'schema'
        cmd = [str(RAIZ / 'bin/tp3'), '--instancia', str(instancia), '--metodo', 'Hbase',
               '--config', str(self.config), '--semente', '1001', '--cpu', '2', '--saida', str(pasta), '--salvar-solucao']
        self.rodar(cmd)
        esperado = {'metodo': 'Hbase'}
        config = runner.configuracao(self.config)
        arquivo = next(p for p in pasta.glob('*.csv') if not p.name.endswith('.solucao.csv'))
        original = arquivo.read_text()
        linhas = original.splitlines()
        cab = linhas[0].split(','); valores = linhas[1].split(',')
        removido = cab.index('tentativas_basicas')
        arquivo.write_text(','.join(cab[:removido]+cab[removido+1:])+'\n'+','.join(valores[:removido]+valores[removido+1:])+'\n')
        with self.assertRaises(ValueError):
            runner.validar(pasta, instancia, esperado, config)
        valores[cab.index('K_60')] = ''; valores[cab.index('desvio_60')] = ''
        arquivo.write_text(linhas[0]+'\n'+','.join(valores)+'\n')
        with self.assertRaises(ValueError):
            runner.validar(pasta, instancia, esperado, config)

    def test_falha_nao_publica(self):
        cmd = self.cmd.copy(); cmd[cmd.index('--cpu')+1] = '1e-300'
        self.rodar(cmd, codigo=1)
        self.assertEqual(list((self.lote / 'execucoes').iterdir()), [])
        self.assertTrue(list((self.lote / '.pendentes').glob('*/stderr.txt')))


if __name__ == '__main__':
    unittest.main()
