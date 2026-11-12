"""Executa a grade pré-definida e congela uma configuração comum às propostas."""

import argparse
import csv
import json
from pathlib import Path
import statistics
import subprocess
import sys

from executar_experimentos import RAIZ, PROPOSTAS, sha, conferir, configuracao
from validar_execucao import exigir, linha_csv

OPCOES = ['base', 'chapas3', 'reinicios10', 'reparo2000']
CPU = 3
SEMENTE = 1001


def criterio(r):
    return (r['desvio_medio'], -r['alcance_lb'], r['tempo_melhor_mediano'], r['cpu_media'], r['id'])


def gravar_imutavel(caminho, conteudo):
    dados = conteudo.encode()
    if caminho.exists():
        exigir(caminho.read_bytes() == dados, f'Congelamento existente diverge: {caminho}')
        return
    with caminho.open('xb') as f:
        f.write(dados)
    caminho.chmod(0o444)


def resumir(id_config, linhas):
    return dict(id=id_config, execucoes=len(linhas),
                K_medio=statistics.mean(int(r['K']) for r in linhas),
                desvio_medio=statistics.mean(float(r['desvio']) for r in linhas),
                alcance_lb=statistics.mean(int(r['alcancou_lb']) for r in linhas),
                tempo_melhor_mediano=statistics.median(float(r['tempo_melhor']) for r in linhas),
                cpu_media=statistics.mean(float(r['tempo_total']) for r in linhas))


def analisar():
    resumos, por_metodo, contratos = [], [], {}
    piloto = list(csv.DictReader((RAIZ / 'instances/manifests/piloto.csv').open()))
    ids = {r['identificador'] for r in piloto}
    ambiente = None
    for opcao in OPCOES:
        cfg = RAIZ / f'config/calibracao/{opcao}.cfg'
        config = configuracao(cfg)
        lote = RAIZ / 'results/calibration' / config['id']
        contrato_path = lote / 'contrato.json'
        contrato = json.loads(contrato_path.read_text())
        exigir(contrato['modo'] == 'calibration' and contrato['cpu'] == CPU and contrato['config_sha256'] == sha(cfg), 'Contrato fora do plano.')
        exigir(contrato['manifestos']['piloto'] == sha(RAIZ / 'instances/manifests/piloto.csv'), 'Piloto alterado.')
        if ambiente is None:
            ambiente = contrato['ambiente']
        exigir(contrato['ambiente'] == ambiente, 'Ambiente/código diferente entre opções.')
        exigir(sha(lote / 'config.cfg') == sha(cfg), 'Configuração do lote alterada.')
        esperadas = {(i, m, SEMENTE) for i in ids for m in PROPOSTAS}
        tarefas = contrato['tarefas']
        exigir(len(tarefas) == 40 and {(t['instancia'], t['metodo'], t['semente']) for t in tarefas} == esperadas, 'Matriz fora do plano.')
        pastas = list((lote / 'execucoes').iterdir())
        exigir(len(pastas) == 40, 'Matriz incompleta ou com saídas excedentes.')
        linhas = []
        for t in tarefas:
            pasta = lote / 'execucoes' / '__'.join(str(t[k]) for k in ['instancia', 'metodo', 'semente'])
            conferir(pasta, t, lote / 'config.cfg', config, CPU, sha(contrato_path))
            arquivo = next(p for p in pasta.glob('*.csv') if not p.name.endswith('.solucao.csv'))
            linhas.append(linha_csv(arquivo))
        resumos.append(resumir(config['id'], linhas))
        por_metodo.extend(dict(metodo=m, **resumir(config['id'], [r for r in linhas if r['metodo'] == m])) for m in PROPOSTAS)
        contratos[config['id']] = sha(contrato_path)
    escolhida = min(resumos, key=criterio)
    origem = next(RAIZ / f'config/calibracao/{o}.cfg' for o in OPCOES if configuracao(RAIZ / f'config/calibracao/{o}.cfg')['id'] == escolhida['id'])
    texto = origem.read_text().replace('id='+escolhida['id'], 'id=congelada_v1').replace('estado=provisorio', 'estado=congelado')
    congelada = RAIZ / 'config/congelada_v1.cfg'
    gravar_imutavel(congelada, texto)
    selo = {'versao': 1, 'config_sha256': sha(congelada), 'escolhida': escolhida, 'contratos_sha256': contratos,
            'plano_sha256': sha(RAIZ / 'docs/calibracao.md'), 'sementes_sha256': sha(RAIZ / 'config/sementes.txt'),
            'criterio': ['desvio_medio', '-alcance_lb', 'tempo_melhor_mediano', 'cpu_media', 'id'],
            'cpu_calibracao': CPU, 'sementes_calibracao': [SEMENTE], 'execucoes_validas': 160}
    gravar_imutavel(RAIZ / 'config/congelada_v1.json', json.dumps(selo, indent=2, sort_keys=True)+'\n')
    destino = RAIZ / 'results/calibration'
    for nome, linhas in [('resumo', resumos), ('por_metodo', por_metodo)]:
        with (destino / (nome+'.csv')).open('w', newline='') as f:
            escritor = csv.DictWriter(f, fieldnames=list(linhas[0])); escritor.writeheader(); escritor.writerows(linhas)
    print(json.dumps(escolhida, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument('--executar', action='store_true')
    grupo.add_argument('--analisar', action='store_true')
    args = parser.parse_args()
    if args.executar:
        for opcao in OPCOES:
            subprocess.run([sys.executable, str(RAIZ / 'scripts/executar_experimentos.py'), '--modo', 'calibration',
                            '--config', str(RAIZ / f'config/calibracao/{opcao}.cfg'), '--cpu', str(CPU),
                            '--sementes', str(SEMENTE)], cwd=RAIZ, check=True)
    else:
        analisar()


if __name__ == '__main__':
    main()
