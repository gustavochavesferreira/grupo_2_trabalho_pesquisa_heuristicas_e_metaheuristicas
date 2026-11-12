"""Cataloga os arquivos originais e aplica a seleção do TP3, sem dependências externas."""

import argparse
import csv
import hashlib
from pathlib import Path
import re
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
CAMPOS = ['caminho', 'familia', 'identificador', 'numero_tipos', 'total_copias',
          'largura', 'altura', 'classe', 'tamanho', 'replica', 'sha256']


def identifica(caminho):
    nome = caminho.name
    if re.fullmatch(r'A([1-9]|[1-3][0-9]|4[0-3])\.ins2D', nome):
        return 'A', '', '', ''
    if re.fullmatch(r'BENG(0[1-9]|10)\.ins2D', nome):
        return 'BENG', '', '', ''
    match = re.fullmatch(r'cl_(0[1-9]|10)_(020|040|060|080|100)_(0[1-9]|10)\.ins2D', nome)
    if match:
        classe, tamanho, replica = map(int, match.groups())
        return 'CLASS', classe, tamanho, replica
    raise ValueError(f'{caminho}: nome de instância não reconhecido.')


def verifica_selecao(piloto, final):
    def chaves(linhas):
        return {(r['familia'], r['identificador']) for r in linhas}
    if len(piloto) != 10 or len(final) != 153:
        raise ValueError('Contagens incorretas: esperadas 10 instâncias-piloto e 153 finais.')
    if len(chaves(piloto)) != 10 or len(chaves(final)) != 153 or chaves(piloto) & chaves(final):
        raise ValueError('Duplicação ou interseção entre piloto e conjunto final.')
    for linhas, esperado in [(piloto, {'A': 5, 'CLASS': 5}), (final, {'A': 38, 'BENG': 10, 'CLASS': 105})]:
        contagens = {familia: sum(r['familia'] == familia for r in linhas) for familia in esperado}
        if contagens != esperado:
            raise ValueError(f'Contagens por família incorretas: {contagens}.')


def cataloga(origem, leitor):
    if not origem.is_dir():
        raise ValueError(f'Diretório de instâncias ausente: {origem}')
    arquivos = []
    registros = []
    vistos = set()
    for caminho in sorted(origem.rglob('*')):
        if not caminho.is_file():
            continue
        if caminho.name in {'README.md', 'format_description.txt'}:
            continue
        familia, classe, tamanho, replica = identifica(caminho)
        chave = (familia, caminho.stem)
        if chave in vistos:
            raise ValueError(f'Instância duplicada: {caminho.stem} ({caminho}).')
        vistos.add(chave)
        arquivos.append(caminho)
        registros.append(dict(caminho=caminho.relative_to(origem).as_posix(), familia=familia,
                              identificador=caminho.stem, classe=classe, tamanho=tamanho, replica=replica))

    obrigatorios = {('A', f'A{i}') for i in range(1, 44)} | {('BENG', f'BENG{i:02}') for i in range(1, 11)}
    obrigatorios |= {('CLASS', f'cl_{c:02}_{n:03}_{r:02}') for c in range(1, 11)
                     for n in (20, 40, 60, 80, 100) for r in (1, 6)}
    obrigatorios |= {('CLASS', f'cl_{c:02}_060_02') for c in range(1, 11)}
    ausentes = sorted(obrigatorios - vistos)
    if ausentes:
        raise ValueError('Instâncias obrigatórias ausentes: ' + ', '.join(nome for _, nome in ausentes))

    processo = subprocess.run([str(leitor), *map(str, arquivos)], capture_output=True, text=True, check=False)
    if processo.returncode:
        raise ValueError('Falha no leitor C++: ' + processo.stderr.strip())
    metadados = list(csv.reader(processo.stdout.splitlines()))
    if len(metadados) != len(registros):
        raise ValueError('Quantidade de registros incompatível com a saída do leitor C++.')
    for registro, caminho, dados in zip(registros, arquivos, metadados):
        if len(dados) != 4:
            raise ValueError('Saída inválida do leitor C++.')
        registro.update(zip(('numero_tipos', 'total_copias', 'largura', 'altura'), map(int, dados)))
        if registro['familia'] in {'CLASS', 'BENG'} and registro['numero_tipos'] != registro['total_copias']:
            raise ValueError(f'{caminho}: esperadas demandas unitárias.')
        if registro['familia'] == 'CLASS' and registro['total_copias'] != registro['tamanho']:
            raise ValueError(f'{caminho}: tamanho do nome difere do número de cópias.')
        registro['sha256'] = hashlib.sha256(caminho.read_bytes()).hexdigest()

    ordenadas_a = sorted((r for r in registros if r['familia'] == 'A'), key=lambda r: (r['total_copias'], r['identificador']))
    piloto_a = {ordenadas_a[i]['identificador'] for i in (0, 10, 21, 32, 42)}
    piloto, final = [], []
    for r in registros:
        if r['familia'] == 'A':
            (piloto if r['identificador'] in piloto_a else final).append(r)
        elif r['familia'] == 'BENG':
            final.append(r)
        elif r['replica'] == 2 and r['tamanho'] == 60:
            (piloto if r['classe'] % 2 else final).append(r)
        elif r['replica'] in (1, 6):
            final.append(r)
    verifica_selecao(piloto, final)
    return registros, piloto, final


def grava(destino, linhas):
    with destino.open('w', newline='', encoding='utf-8') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS, lineterminator='\n')
        escritor.writeheader()
        escritor.writerows(linhas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=RAIZ / 'instances/source')
    parser.add_argument('--output', type=Path, default=RAIZ / 'instances/manifests')
    parser.add_argument('--leitor', type=Path, default=RAIZ / 'bin/metadados_instancia')
    args = parser.parse_args()
    try:
        conjuntos = cataloga(args.source.resolve(), args.leitor.resolve())
        args.output.mkdir(parents=True, exist_ok=True)
        for nome, linhas in zip(('catalogo', 'piloto', 'final'), conjuntos):
            grava(args.output / f'{nome}.csv', linhas)
        print(f'Catálogo: {len(conjuntos[0])}; piloto: 10; final: 153. Contagens e disjunção: OK.')
    except (ValueError, OSError) as erro:
        print(f'Erro: {erro}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
