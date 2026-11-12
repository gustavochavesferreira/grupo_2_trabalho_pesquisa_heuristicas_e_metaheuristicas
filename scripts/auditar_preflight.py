"""Audita a matriz técnica, sem produzir comparações de qualidade entre métodos."""

import argparse
from collections import Counter
import json
import hashlib
import subprocess
import sys
from pathlib import Path

from executar_experimentos import RAIZ, METODOS, conferir, configuracao, ler_manifesto, sha
from catalogar_instancias import verifica_selecao
from validar_execucao import exigir
from verificar_congelamento import verificar


def auditar(lote):
    verificar()
    piloto = ler_manifesto(RAIZ / 'instances/manifests/piloto.csv')
    final = ler_manifesto(RAIZ / 'instances/manifests/final.csv')
    verifica_selecao(piloto, final)
    contrato_path = lote / 'contrato.json'
    contrato = json.loads(contrato_path.read_text())
    exigir(contrato['modo'] == 'preflight' and contrato['cpu'] == 3, 'Protocolo diferente da pré-execução definida.')
    exigir(contrato['config_sha256'] == sha(RAIZ / 'config/congelada_v1.cfg') == sha(lote / 'config.cfg'), 'Configuração congelada divergente.')
    for nome in ['piloto', 'final']:
        exigir(contrato['manifestos'][nome] == sha(RAIZ / f'instances/manifests/{nome}.csv'), 'Manifesto alterado.')
    exigir(contrato['sementes_sha256'] == sha(RAIZ / 'config/sementes.txt'), 'Sementes alteradas.')
    exigir(contrato['ambiente']['executavel_sha256'] == sha(RAIZ / 'bin/tp3'), 'Executável difere do lote.')
    esperadas = {(r['identificador'], r['familia'], m, 1001) for r in final for m in METODOS}
    tarefas = contrato['tarefas']
    exigir(len(tarefas) == 918 and {(t['instancia'], t['familia'], t['metodo'], t['semente']) for t in tarefas} == esperadas, 'Matriz incompleta, duplicada ou fora do conjunto final.')
    pastas = {p.name for p in (lote / 'execucoes').iterdir()}
    nomes = {'__'.join(str(t[k]) for k in ['instancia', 'metodo', 'semente']) for t in tarefas}
    exigir(pastas == nomes, 'Execuções ausentes ou excedentes.')
    config = configuracao(lote / 'config.cfg')
    digest = sha(contrato_path)
    for i, t in enumerate(tarefas, 1):
        pasta = lote / 'execucoes' / '__'.join(str(t[k]) for k in ['instancia', 'metodo', 'semente'])
        conferir(pasta, t, lote / 'config.cfg', config, 3, digest)
        if i % 150 == 0:
            print(f'Auditadas {i}/918 execuções.', flush=True)
    return {'versao': 1, 'uso': 'verificacao_tecnica_sem_resultados_cientificos', 'valido': True,
            'instancias': 153, 'execucoes_validas': 918, 'metodos': METODOS, 'semente': 1001, 'cpu': 3,
            'familias_instancias': dict(Counter(r['familia'] for r in final)), 'intersecao_piloto': 0,
            'contrato_sha256': digest, 'config_sha256': sha(lote / 'config.cfg'),
            'ambiente': contrato['ambiente'], 'retomada_verificada': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lote', type=Path, default=RAIZ / 'results/preflight/congelada_v1')
    parser.add_argument('--verificar-retomada', action='store_true')
    args = parser.parse_args()
    lote = args.lote.resolve()
    dados = auditar(lote)
    if args.verificar_retomada:
        recibos = sorted((lote / 'execucoes').glob('*/concluida.json'))
        antes = {p.parent.name: sha(p) for p in recibos}
        log = lote.parent / 'retomada.log'
        with log.open('w') as saida:
            subprocess.run([sys.executable, str(RAIZ / 'scripts/executar_experimentos.py'),
                            '--modo', 'preflight', '--config', str(RAIZ / 'config/congelada_v1.cfg'),
                            '--cpu', '3', '--sementes', '1001', '--saida', str(lote.parent.parent)],
                           cwd=RAIZ, stdout=saida, stderr=subprocess.STDOUT, check=True)
        depois = {p.parent.name: sha(p) for p in sorted((lote / 'execucoes').glob('*/concluida.json'))}
        exigir(antes == depois and len(antes) == 918, 'Retomada modificou recibos ou a matriz.')
        exigir('918 válidas; 918 puladas; 0 executadas.' in log.read_text(), 'Retomada não pulou exatamente 918 execuções.')
        prova = {'contrato_sha256': dados['contrato_sha256'], 'puladas': 918, 'executadas': 0,
                 'recibos_antes_depois_sha256': hashlib.sha256(json.dumps(antes, sort_keys=True).encode()).hexdigest(),
                 'log_sha256': sha(log)}
        (lote.parent / 'retomada.json').write_text(json.dumps(prova, indent=2, sort_keys=True)+'\n')
        dados = auditar(lote)
    destino = RAIZ / 'results/preflight/integridade.json'
    # A retomada é registrada separadamente, somente depois de conferir os recibos.
    retomada = destino.parent / 'retomada.json'
    if retomada.exists():
        r = json.loads(retomada.read_text())
        exigir(r['contrato_sha256'] == dados['contrato_sha256'] and r['puladas'] == 918 and r['executadas'] == 0, 'Retomada incompatível.')
        dados['retomada_verificada'] = True
    destino.write_text(json.dumps(dados, indent=2, sort_keys=True)+'\n')
    print('Matriz de 918 execuções validada; sem análise comparativa de qualidade.')


if __name__ == '__main__':
    main()
