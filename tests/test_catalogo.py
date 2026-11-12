"""Verifica seleção e rejeições usando cópias temporárias dos dados reais fornecidos."""

import csv
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'scripts'))
from catalogar_instancias import cataloga, grava, verifica_selecao


class TestCatalogo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.origem = RAIZ / 'instances/source'
        cls.leitor = RAIZ / 'bin/metadados_instancia'
        cls.conjuntos = cataloga(cls.origem, cls.leitor)

    def test_selecao_e_metadados(self):
        catalogo, piloto, final = self.conjuntos
        verifica_selecao(piloto, final)
        ordenadas = sorted((r for r in catalogo if r['familia'] == 'A'),
                           key=lambda r: (r['total_copias'], r['identificador']))
        self.assertEqual({r['identificador'] for r in piloto if r['familia'] == 'A'},
                         {ordenadas[i]['identificador'] for i in (0, 10, 21, 32, 42)})
        for linhas, classes in ((piloto, {1, 3, 5, 7, 9}), (final, {2, 4, 6, 8, 10})):
            self.assertEqual({(r['classe'], r['tamanho'], r['replica']) for r in linhas
                              if r['familia'] == 'CLASS' and r['replica'] == 2},
                             {(c, 60, 2) for c in classes})
        self.assertEqual({(r['classe'], r['tamanho'], r['replica']) for r in final
                          if r['familia'] == 'CLASS' and r['replica'] in (1, 6)},
                         {(c, n, r) for c in range(1, 11) for n in (20, 40, 60, 80, 100) for r in (1, 6)})
        for registro in catalogo:
            caminho = self.origem / registro['caminho']
            self.assertEqual(registro['sha256'], hashlib.sha256(caminho.read_bytes()).hexdigest())
            self.assertFalse(Path(registro['caminho']).is_absolute())

    def test_manifestos_reproduziveis(self):
        repetidos = cataloga(self.origem, self.leitor)
        self.assertEqual(self.conjuntos, repetidos)
        with tempfile.TemporaryDirectory() as tmp:
            for nome, linhas in zip(('catalogo', 'piloto', 'final'), repetidos):
                destino = Path(tmp) / f'{nome}.csv'
                grava(destino, linhas)
                self.assertEqual(destino.read_bytes(), (RAIZ / 'instances/manifests' / destino.name).read_bytes())
                with destino.open() as arquivo:
                    self.assertEqual(len(list(csv.DictReader(arquivo))), len(linhas))

    def test_falhas_com_dados_reais(self):
        with tempfile.TemporaryDirectory() as tmp:
            origem = Path(tmp) / 'source'
            shutil.copytree(self.origem, origem)
            registro = next(r for r in self.conjuntos[0] if r['familia'] == 'BENG')
            caminho = origem / registro['caminho']
            conteudo = caminho.read_bytes()
            caminho.unlink()
            with self.assertRaisesRegex(ValueError, 'ausentes'):
                cataloga(origem, self.leitor)
            caminho.write_bytes(conteudo)
            duplicada = origem / caminho.name
            duplicada.write_bytes(conteudo)
            with self.assertRaisesRegex(ValueError, 'duplicada'):
                cataloga(origem, self.leitor)
            duplicada.unlink()
            desconhecida = origem / 'nome_invalido.ins2D'
            desconhecida.write_bytes(conteudo)
            with self.assertRaisesRegex(ValueError, 'não reconhecido'):
                cataloga(origem, self.leitor)
            desconhecida.unlink()
            caminho.write_bytes(conteudo + b'\nregistro excedente\n')
            with self.assertRaisesRegex(ValueError, r'leitor C\+\+'):
                cataloga(origem, self.leitor)

    def test_auditoria_rejeita_sobreposicao_e_contagens(self):
        _, piloto, final = self.conjuntos
        with self.assertRaises(ValueError):
            verifica_selecao(piloto[:-1], final)
        with self.assertRaises(ValueError):
            verifica_selecao(piloto, [piloto[0], *final[1:]])
        with self.assertRaises(ValueError):
            verifica_selecao(piloto, [final[0], *final[:-1]])


if __name__ == '__main__':
    unittest.main()
