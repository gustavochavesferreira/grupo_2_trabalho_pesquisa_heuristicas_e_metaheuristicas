"""Integra os seis métodos pela CLI e confere soluções exportadas sem geometria C++."""

import csv
from pathlib import Path
import subprocess
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
METODOS = ['Hbase', 'Hext', 'Hint', 'Hcomb', 'Haleat', 'RLS-f7']


def ler_instancia(caminho):
    linhas = [linha.split() for linha in caminho.read_text().splitlines() if linha.strip()]
    w, h = map(int, linhas[1])
    copias = {}
    for linha in linhas[2:]:
        tipo, largura, altura, demanda = map(int, linha[:4])
        for _ in range(demanda):
            copias[len(copias)+1] = (tipo, largura, altura)
    return w, h, copias


def ler_resultado(pasta):
    arquivos = [p for p in pasta.glob('*.csv') if not p.name.endswith('.solucao.csv')]
    if len(arquivos) != 1:
        raise AssertionError('Era esperado um único CSV de resultado.')
    with arquivos[0].open(newline='') as f:
        leitor = csv.DictReader(f)
        cabecalho = leitor.fieldnames
        linhas = list(leitor)
    if len(linhas) != 1 or len(set(cabecalho)) != len(cabecalho) or None in linhas[0] or None in linhas[0].values():
        raise AssertionError('CSV inválido, truncado ou com campos excedentes.')
    with (pasta / linhas[0]['solucao_arquivo']).open(newline='') as f:
        solucao = list(csv.DictReader(f))
    return cabecalho, linhas[0], solucao


class IntegracaoCLI(unittest.TestCase):
    def conferir_geometria(self, instancia, r, linhas):
        w, h, copias = ler_instancia(instancia)
        self.assertEqual(len(linhas), len(copias))
        vistas = set()
        chapas = {}
        for linha in linhas:
            p = {chave: int(valor) for chave, valor in linha.items()}
            self.assertEqual(p['versao'], 1)
            self.assertIn(p['copia_id'], copias)
            self.assertNotIn(p['copia_id'], vistas)
            vistas.add(p['copia_id'])
            tipo, largura, altura = copias[p['copia_id']]
            self.assertEqual(p['tipo_id'], tipo)
            self.assertIn(p['rotacionada'], [0, 1])
            if p['rotacionada']:
                largura, altura = altura, largura
            self.assertEqual((p['largura'], p['altura']), (largura, altura))
            self.assertTrue(0 <= p['x'] <= w-largura and 0 <= p['y'] <= h-altura)
            chapas.setdefault(p['chapa'], []).append(p)
        self.assertEqual(vistas, set(copias))
        self.assertEqual(set(chapas), set(range(int(r['K']))))
        for pecas in chapas.values():
            for j, a in enumerate(pecas):
                for b in pecas[j+1:]:
                    sobrepoe = (a['x'] < b['x']+b['largura'] and b['x'] < a['x']+a['largura'] and
                                a['y'] < b['y']+b['altura'] and b['y'] < a['y']+a['altura'])
                    self.assertFalse(sobrepoe, 'Sobreposição na solução exportada.')
        if r['metodo'] == 'RLS-f7':
            # Soma por colunas, independente da integração por intervalos do C++.
            ultima = chapas[int(r['K'])-1]
            perfil = sum(max([p['y']+p['altura'] for p in ultima if p['x'] <= x < p['x']+p['largura']], default=0) for x in range(w))
            self.assertEqual(int(r['area_perfil']), perfil)
            self.assertEqual(int(r['f7']), w*h*(int(r['K'])-1)+perfil)

    def test_matriz_exportada_e_reproduzida(self):
        with tempfile.TemporaryDirectory(prefix='tp3_integracao_cli_') as tmp:
            pasta = Path(tmp)
            config = pasta / 'integracao.cfg'
            texto = (RAIZ / 'config/provisoria.cfg').read_text().replace('max_reinicios=5', 'max_reinicios=1').replace('max_avaliacoes_reparo=1000', 'max_avaliacoes_reparo=40').replace('rls_max_avaliacoes=100000000', 'rls_max_avaliacoes=80')
            config.write_text(texto)
            padrao = None
            ignorados = {'tempo_total', 'tempo_melhor', 'limite_cpu_atingido'}
            for nome in ['valida.txt', 'integracao/reducao.txt', 'integracao/limite_inicial.txt', 'integracao/orcamento.txt']:
                instancia = RAIZ / 'tests/data' / nome
                for metodo in METODOS:
                    anteriores = None
                    for repeticao in range(2):
                        saida = pasta / instancia.stem / metodo / str(repeticao)
                        comando = [str(RAIZ / 'bin/tp3'), '--instancia', str(instancia), '--metodo', metodo,
                                   '--config', str(config), '--semente', '1001', '--cpu', '2',
                                   '--saida', str(saida), '--salvar-solucao']
                        p = subprocess.run(comando, cwd=RAIZ, text=True, capture_output=True, timeout=15)
                        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
                        cabecalho, r, solucao = ler_resultado(saida)
                        if padrao is None:
                            padrao = cabecalho
                        self.assertEqual(cabecalho, padrao, 'Métodos com formatos diferentes.')
                        self.assertEqual(r['metodo'], metodo)
                        self.assertEqual(r['instancia'], instancia.stem)
                        self.assertEqual(r['familia'], 'OUTRA')
                        self.assertEqual(r['versao'], '1')
                        self.assertEqual(r['validada'], '1')
                        self.assertEqual(r['controle_auxiliar'], '1' if metodo == 'Haleat' else '0')
                        self.assertEqual(r['config_estado'], 'provisorio')
                        self.assertEqual(r['rls_max_avaliacoes'], '80')
                        self.assertEqual(r['max_avaliacoes_reparo'], '40')
                        self.assertGreaterEqual(int(r['K']), int(r['LBref']))
                        self.assertAlmostEqual(float(r['desvio']), 100*(int(r['K'])-int(r['LBref']))/int(r['LBref']))
                        self.assertEqual(r['alcancou_lb'], '1' if r['K'] == r['LBref'] else '0')
                        self.assertLessEqual(float(r['tempo_melhor']), float(r['tempo_total']))
                        for t in ['0_1', '1', '5', '10', '30', '60']:
                            self.assertEqual(r['K_'+t], r['K'])
                            self.assertEqual(r['desvio_'+t], r['desvio'])
                        if metodo in ['Hext', 'Hcomb']:
                            self.assertGreaterEqual(int(r['historico_atualizacoes']), 0)
                            self.assertEqual(r['historico_reinicios'], r['tentativas_reducao'])
                        else:
                            self.assertEqual(r['historico_atualizacoes'], '')
                        if metodo in ['Hint', 'Hcomb', 'Haleat']:
                            self.assertLessEqual(int(r['decodificacoes_extras']), 16*int(r['ativacoes_internas']))
                        else:
                            self.assertEqual(r['ativacoes_internas'], '')
                        self.conferir_geometria(instancia, r, solucao)
                        if nome.endswith('limite_inicial.txt'):
                            self.assertEqual(r['motivo_parada'], 'limite_inferior')
                            self.assertEqual(r['K'], '1')
                            self.assertEqual(r['avaliacoes'], '1' if metodo == 'RLS-f7' else '0')
                        if nome.endswith('orcamento.txt'):
                            self.assertEqual(r['K'], '3')
                            self.assertEqual(r['motivo_parada'], 'limite_avaliacoes' if metodo == 'RLS-f7' else 'orcamento_reparo')
                        retrato = ({chave: valor for chave, valor in r.items() if chave not in ignorados}, solucao)
                        if anteriores is not None:
                            self.assertEqual(retrato, anteriores, f'Reprodução divergente: {metodo}, {nome}')
                        anteriores = retrato


    def test_cpu_com_e_sem_incumbente(self):
        with tempfile.TemporaryDirectory(prefix='tp3_cpu_cli_') as tmp:
            pasta = Path(tmp)
            config = pasta / 'cpu.cfg'
            texto = (RAIZ / 'config/provisoria.cfg').read_text().replace('max_reinicios=5', 'max_reinicios=1000000').replace('max_avaliacoes_reparo=1000', 'max_avaliacoes_reparo=1000000')
            config.write_text(texto)
            instancia = RAIZ / 'tests/data/integracao/orcamento.txt'
            for metodo in METODOS:
                for cpu, codigo in [('0.02', 0), ('1e-300', 3)]:
                    saida = pasta / metodo / cpu
                    comando = [str(RAIZ / 'bin/tp3'), '--instancia', str(instancia), '--metodo', metodo,
                               '--config', str(config), '--semente', '1001', '--cpu', cpu,
                               '--saida', str(saida), '--salvar-solucao']
                    p = subprocess.run(comando, cwd=RAIZ, text=True, capture_output=True, timeout=15)
                    self.assertEqual(p.returncode, codigo, p.stdout+p.stderr)
                    if codigo == 3:
                        self.assertIn('primeira solução completa', p.stderr)
                        self.assertFalse(saida.exists())
                    else:
                        _, r, solucao = ler_resultado(saida)
                        self.assertEqual(r['motivo_parada'], 'limite_cpu')
                        self.assertEqual(r['limite_cpu_atingido'], '1')
                        self.assertEqual(r['alcancou_lb'], '0')
                        self.assertGreaterEqual(float(r['tempo_total']), 0.02)
                        self.conferir_geometria(instancia, r, solucao)


if __name__ == '__main__':
    unittest.main()
