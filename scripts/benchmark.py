"""Executa as três famílias do benchmark final com progresso e retomada."""

import argparse
from collections import Counter
import json
import subprocess
import sys
import math
import time

from executar_experimentos import RAIZ, METODOS, SEMENTES, sha, conferir, configuracao, ler_manifesto
from piloto import executar_com_progresso, conferir_prazo
from validar_execucao import exigir, linha_csv
from tabela_comparacao import gravar_tabela
from verificar_congelamento import verificar


def preparar():
    verificar()
    selo = json.loads((RAIZ / 'config/h_estrela_v2.json').read_text())
    exigir(selo['execucoes_validas'] == 400, 'Seleção de H* sem piloto completo.')
    exigir(selo['config_sha256'] == sha(RAIZ / 'config/congelada_v2.cfg'), 'Configuração difere da seleção de H*.')
    exigir(selo['sementes_sha256'] == sha(RAIZ / 'config/sementes.txt'), 'Sementes diferem da seleção de H*.')
    exigir(selo['piloto_sha256'] == sha(RAIZ / 'instances/manifests/piloto.csv'), 'Manifesto piloto alterado.')
    exigir(selo['contrato_sha256'] == sha(RAIZ / 'results/pilot/congelada_v2/contrato.json'), 'Contrato do piloto alterado.')
    return selo


def auditar(selo, prazo=None):
    lote = RAIZ / 'results/final/congelada_v2'
    contrato_path = lote / 'contrato.json'
    contrato = json.loads(contrato_path.read_text())
    config = configuracao(lote / 'config.cfg')
    exigir(contrato['modo'] == 'final' and contrato['cpu'] == 60, 'Protocolo final divergente.')
    exigir(contrato['config_sha256'] == selo['config_sha256'] == sha(lote / 'config.cfg'), 'Configuração final divergente.')
    final = ler_manifesto(RAIZ / 'instances/manifests/final.csv')
    esperadas = {(r['identificador'], r['familia'], m, s) for r in final for m in METODOS for s in SEMENTES}
    tarefas = contrato['tarefas']
    exigir(len(tarefas) == 9180 and {(t['instancia'], t['familia'], t['metodo'], t['semente']) for t in tarefas} == esperadas, 'Matriz final incorreta.')
    nomes = {'__'.join(str(t[k]) for k in ['instancia', 'metodo', 'semente']) for t in tarefas}
    exigir({p.name for p in (lote / 'execucoes').iterdir()} == nomes, 'Resultados finais ausentes ou excedentes.')
    digest = sha(contrato_path)
    linhas = []
    for i, t in enumerate(tarefas, 1):
        conferir_prazo(prazo)
        pasta = lote / 'execucoes' / '__'.join(str(t[k]) for k in ['instancia', 'metodo', 'semente'])
        conferir(pasta, t, lote / 'config.cfg', config, 60, digest)
        linhas.append(linha_csv(next(p for p in pasta.glob('*.csv') if not p.name.endswith('.solucao.csv'))))
        if i % 500 == 0 or i == len(tarefas):
            print(f'Auditoria final: {i}/9180.', flush=True)
    contagens = dict(Counter(t['familia'] for t in tarefas))
    exigir(contagens == {'A': 2280, 'BENG': 600, 'CLASS': 6300}, 'Contagens por família divergentes.')
    gravar_tabela(lote/'tabela_comparacao.csv',linhas,METODOS,{r['identificador'] for r in final},SEMENTES)
    relatorio = {'valido': True, 'execucoes': 9180, 'familias': contagens,
                 'contrato_sha256': digest, 'h_estrela_sha256': sha(RAIZ / 'config/h_estrela_v2.json')}
    (lote / 'integridade_familias.json').write_text(json.dumps(relatorio, indent=2)+'\n')
    print('Benchmark concluído: A 2280/2280; BENG 600/600; CLASS 6300/6300. Todas as soluções validadas.')
    print(f'Resultados salvos em {lote}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument('--planejar', action='store_true', help='Confere o plano sem executar algoritmos.')
    grupo.add_argument('--analisar', action='store_true', help='Audita resultados completos e gera tabela sem executar.')
    parser.add_argument('--max-minutos',type=float,help='Teto total desta chamada; padrão sem teto de parede.')
    args = parser.parse_args()
    if args.max_minutos is not None and (not math.isfinite(args.max_minutos) or args.max_minutos<=0):
        parser.error('Teto deve ser positivo e finito.')
    prazo = None if args.max_minutos is None else time.monotonic()+60*args.max_minutos
    try:
        verificar()
        comando = [sys.executable, '-u', str(RAIZ / 'scripts/executar_experimentos.py'),
                   '--modo', 'final', '--config', str(RAIZ / 'config/congelada_v2.cfg')]
        if args.planejar:
            plano = json.loads(subprocess.check_output(comando + ['--planejar'], cwd=RAIZ, text=True))
            exigir(plano['execucoes'] == 9180, 'Plano incompleto.')
            print('Plano: 153 instâncias × 6 métodos × 10 sementes × 60 s de CPU.')
            print('A: 2280; BENG: 600; CLASS: 6300. Total: 9180 execuções.')
            return 0
        selo = preparar()
        print('Iniciando/retomando benchmark: 9180 execuções sequenciais.', flush=True)
        if not args.analisar:
            executar_com_progresso(comando,prazo)
        auditar(selo,prazo)
    except TimeoutError as erro:
        print(str(erro),file=sys.stderr)
        return 124
    except KeyboardInterrupt:
        print('Interrompido. Repita python3 scripts/benchmark.py para retomar.', file=sys.stderr)
        return 130
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as erro:
        print(f'Erro: {erro}. Resultados completos preservados.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
