"""Um comando para executar, retomar, auditar e selecionar H* no piloto formal."""

import argparse
import csv
from fractions import Fraction
import json
import re
from pathlib import Path
import statistics
import subprocess
import sys

from executar_experimentos import RAIZ, PROPOSTAS, SEMENTES, conferir, configuracao, ler_manifesto, sha
from catalogar_instancias import verifica_selecao
from validar_execucao import exigir, linha_csv
from verificar_congelamento import verificar
from calibrar import gravar_imutavel


def barra_progresso(concluidas, total):
    largura = 30
    preenchidas = largura * concluidas // total
    return f"[{'#' * preenchidas}{'-' * (largura - preenchidas)}] {concluidas}/{total} ({100 * concluidas / total:.1f}%)"


def progresso_da_linha(linha):
    evento = re.match(r"\[(\d+)/(\d+)\] (Executando:|Válida, pulando:)", linha)
    if evento:
        indice, total = int(evento[1]), int(evento[2])
        return (indice - 1 if evento[3] == 'Executando:' else indice), total
    final = re.match(r"Lote completo: (\d+) válidas;", linha)
    return (int(final[1]), int(final[1])) if final else None


def executar_com_progresso(comando):
    terminal = sys.stdout.isatty()
    with subprocess.Popen(comando, cwd=RAIZ, stdout=subprocess.PIPE, text=True, bufsize=1) as filho:
        try:
            for linha in filho.stdout:
                progresso = progresso_da_linha(linha)
                if progresso:
                    texto = barra_progresso(*progresso)
                    if terminal:
                        print('\r' + texto + '\033[K', end='', flush=True)
                    else:
                        print(texto, flush=True)
                else:
                    if terminal:
                        print()
                    print(linha, end='', flush=True)
            codigo = filho.wait()
        except BaseException:
            filho.terminate()
            filho.wait()
            raise
        finally:
            if terminal:
                print()
    if codigo:
        raise subprocess.CalledProcessError(codigo, comando)


def resumir(metodo, linhas):
    exigir(len(linhas) == 100, 'Cada método deve ter exatamente 100 resultados.')
    desvio = sum((Fraction(100*(int(r['K'])-int(r['LBref'])), int(r['LBref'])) for r in linhas), Fraction()) / len(linhas)
    return {'metodo': metodo, 'execucoes': len(linhas), 'K_medio': statistics.mean(int(r['K']) for r in linhas),
            'desvio_medio': float(desvio), 'desvio_exato': str(desvio),
            'alcances_lb': sum(int(r['alcancou_lb']) for r in linhas),
            'tempo_melhor_mediano': statistics.median(float(r['tempo_melhor']) for r in linhas)}


def criterio(r):
    return Fraction(r['desvio_exato']), -r['alcances_lb'], r['tempo_melhor_mediano']


def analisar():
    verificar()
    config_path = RAIZ / 'config/congelada_v1.cfg'
    config = configuracao(config_path)
    lote = RAIZ / 'results/pilot' / config['id']
    contrato_path = lote / 'contrato.json'
    contrato = json.loads(contrato_path.read_text())
    piloto = ler_manifesto(RAIZ / 'instances/manifests/piloto.csv')
    final = ler_manifesto(RAIZ / 'instances/manifests/final.csv')
    verifica_selecao(piloto, final)
    exigir(contrato['modo'] == 'pilot' and contrato['cpu'] == 60, 'Contrato não é do piloto formal.')
    exigir(contrato['config_sha256'] == sha(config_path) == sha(lote / 'config.cfg'), 'Configuração congelada divergente.')
    exigir(contrato['sementes_sha256'] == sha(RAIZ / 'config/sementes.txt'), 'Sementes divergentes.')
    for nome in ['piloto', 'final']:
        exigir(contrato['manifestos'][nome] == sha(RAIZ / f'instances/manifests/{nome}.csv'), 'Manifesto alterado.')
    esperadas = {(r['identificador'], r['familia'], m, s) for r in piloto for m in PROPOSTAS for s in SEMENTES}
    tarefas = contrato['tarefas']
    exigir(len(tarefas) == 400 and {(t['instancia'], t['familia'], t['metodo'], t['semente']) for t in tarefas} == esperadas, 'Matriz do piloto incompleta, duplicada ou incorreta.')
    nomes = {'__'.join(str(t[k]) for k in ['instancia', 'metodo', 'semente']) for t in tarefas}
    exigir({p.name for p in (lote / 'execucoes').iterdir()} == nomes, 'Execuções ausentes ou excedentes.')
    digest_contrato = sha(contrato_path)
    linhas = []
    for n, tarefa in enumerate(tarefas, 1):
        pasta = lote / 'execucoes' / '__'.join(str(tarefa[k]) for k in ['instancia', 'metodo', 'semente'])
        conferir(pasta, tarefa, lote / 'config.cfg', config, 60, digest_contrato)
        arquivo = next(p for p in pasta.glob('*.csv') if not p.name.endswith('.solucao.csv'))
        linhas.append(linha_csv(arquivo))
        if n % 100 == 0:
            print(f'Auditadas {n}/400 execuções.', flush=True)
    resumos = [resumir(m, [r for r in linhas if r['metodo'] == m]) for m in PROPOSTAS]
    melhor = min(criterio(r) for r in resumos)
    empatadas = [r['metodo'] for r in resumos if criterio(r) == melhor]
    # Empate nos três critérios preserva a ordem pública das propostas e é informado.
    escolhida = empatadas[0]
    selo = {'versao': 1, 'H_estrela': escolhida, 'empate_total': empatadas, 'execucoes_validas': 400,
            'criterio': ['menor_desvio_medio', 'maior_alcance_lb', 'menor_tempo_melhor_mediano'],
            'desempate_final': 'ordem Hbase, Hext, Hint, Hcomb somente se os três critérios forem idênticos',
            'config_sha256': sha(config_path), 'sementes_sha256': sha(RAIZ / 'config/sementes.txt'),
            'piloto_sha256': sha(RAIZ / 'instances/manifests/piloto.csv'), 'contrato_sha256': sha(contrato_path),
            'ambiente': contrato['ambiente'], 'resumos': resumos}
    gravar_imutavel(RAIZ / 'config/h_estrela_v1.json', json.dumps(selo, indent=2, sort_keys=True)+'\n')
    resumo = lote.parent / 'resumo.csv'
    with resumo.open('w', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=list(resumos[0])); escritor.writeheader(); escritor.writerows(resumos)
    (lote.parent / 'integridade.json').write_text(json.dumps({'valido': True, 'execucoes': 400, 'instancias': 10,
          'metodos': 4, 'sementes': SEMENTES, 'contrato_sha256': sha(contrato_path)}, indent=2)+'\n')
    print(f'Piloto concluído: 400 execuções validadas. H* = {escolhida}.')
    print(f'Resultados e resumo: {lote.parent}')
    print(f'Escolha congelada: {RAIZ / "config/h_estrela_v1.json"}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument('--planejar', action='store_true', help='Somente confere e mostra o plano.')
    grupo.add_argument('--analisar', action='store_true', help='Somente audita resultados já existentes e seleciona H*.')
    args = parser.parse_args()
    try:
        verificar()
        if not args.analisar:
            comando = [sys.executable, str(RAIZ / 'scripts/executar_experimentos.py'), '--modo', 'pilot',
                       '--config', str(RAIZ / 'config/congelada_v1.cfg')]
            if args.planejar:
                comando.append('--planejar')
            if args.planejar:
                subprocess.run(comando, cwd=RAIZ, check=True)
            else:
                executar_com_progresso(comando)
        if not args.planejar:
            analisar()
    except KeyboardInterrupt:
        print('Interrompido. Repita o mesmo comando para retomar.', file=sys.stderr)
        return 130
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as erro:
        print(f'Erro: {erro}. Resultados anteriores preservados; H* não é substituído.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
