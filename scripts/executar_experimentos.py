"""Executa lotes sequenciais, valida e publica cada execução para retomada segura."""

import argparse
import csv
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shlex
import subprocess
import sys
import tempfile
import uuid

from catalogar_instancias import verifica_selecao, identifica
from validar_execucao import validar, exigir

RAIZ = Path(__file__).resolve().parents[1]
PROPOSTAS = ['Hbase', 'Hext', 'Hint', 'Hcomb']
METODOS = PROPOSTAS + ['Haleat', 'RLS-f7']
SEMENTES = list(range(1001, 1011))


def sha(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def agora():
    return datetime.now(timezone.utc).isoformat()


def json_atomico(caminho, dados):
    temporario = caminho.with_name(caminho.name + '.tmp')
    with temporario.open('w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporario, caminho)


@contextmanager
def exclusividade(caminho):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open('a+') as trava:
        try:
            fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Outro orquestrador ou processo de execução ainda mantém a trava global.') from None
        yield trava.fileno()


def processo(comando, fd, stdout, stderr):
    # O filho herda a trava: nem a morte abrupta do pai permite sobrepor outra execução.
    with subprocess.Popen(comando, cwd=RAIZ, stdin=subprocess.DEVNULL, stdout=stdout,
                          stderr=stderr, pass_fds=(fd,)) as filho:
        try:
            return filho.wait()
        except BaseException:
            filho.terminate()
            filho.wait()
            raise


def configuracao(caminho):
    dados = {}
    obrigatorias = {'versao', 'id', 'estado', 'chapas_perturbadas', 'max_reinicios', 'max_avaliacoes_reparo', 'rls_max_avaliacoes'}
    for linha in caminho.read_text().splitlines():
        linha = linha.strip()
        if not linha or linha.startswith('#'):
            continue
        exigir('=' in linha, 'Configuração: esperado chave=valor.')
        chave, valor = map(str.strip, linha.split('=', 1))
        exigir(chave in obrigatorias and chave not in dados and valor, 'Chave de configuração inválida/repetida.')
        dados[chave] = valor
    exigir(set(dados) == obrigatorias and dados['versao'] == '1', 'Configuração incompleta/versão inválida.')
    exigir(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', dados['id']), 'ID de configuração inválido.')
    exigir(dados['estado'] in ['provisorio', 'congelado'], 'Estado de configuração inválido.')
    for chave in obrigatorias - {'versao', 'id', 'estado'}:
        exigir(re.fullmatch('[0-9]+', dados[chave]), 'Parâmetro deve ser inteiro não negativo.')
        valor = int(dados[chave])
        exigir(valor <= 2**64-1, 'Parâmetro fora da faixa.')
        dados[chave] = str(valor)
    exigir(int(dados['chapas_perturbadas']) >= 2 and 1 <= int(dados['rls_max_avaliacoes']) <= 100000000, 'Parâmetros fora da faixa.')
    return dados


def ler_manifesto(caminho):
    import csv
    with caminho.open(newline='') as f:
        return list(csv.DictReader(f))


def planejar(args):
    piloto = ler_manifesto(RAIZ / 'instances/manifests/piloto.csv')
    final = ler_manifesto(RAIZ / 'instances/manifests/final.csv')
    verifica_selecao(piloto, final)
    sementes = [int(l) for l in (RAIZ / 'config/sementes.txt').read_text().splitlines()]
    exigir(sementes == SEMENTES, 'Arquivo de sementes diverge das dez sementes comuns do TP3.')
    config = configuracao(args.config)
    formais = args.modo in ['pilot', 'final']
    if args.modo != 'calibration':
        exigir(config['estado'] == 'congelado', 'Este modo exige configuração congelada; execute a Tarefa 21 antes.')
        exigir(config['rls_max_avaliacoes'] == '100000000', 'Modos posteriores à calibração exigem o teto publicado da RLS.')
    cpu = args.cpu if args.cpu is not None else (60 if formais else 1)
    exigir(math.isfinite(cpu) and cpu > 0 and (not formais or cpu == 60), 'CPU inválida: pilot/final exigem 60 segundos.')
    metodos = args.metodos or (PROPOSTAS if args.modo in ['calibration', 'pilot'] else METODOS)
    sorteios = args.sementes or (sementes if formais else [1001])
    exigir(len(set(metodos)) == len(metodos) and set(metodos) <= set(METODOS), 'Lista de métodos inválida.')
    exigir(len(set(sorteios)) == len(sorteios) and set(sorteios) <= set(sementes), 'Sementes devem pertencer ao conjunto comum, sem repetições.')
    if args.modo in ['calibration', 'pilot']:
        exigir(set(metodos) <= set(PROPOSTAS), 'Calibração/piloto usam somente as quatro propostas.')
    if args.modo == 'pilot':
        exigir(set(metodos) == set(PROPOSTAS) and sorteios == sementes and not args.instancias, 'Piloto exige as dez instâncias, quatro propostas e dez sementes.')
    if args.modo in ['preflight', 'final']:
        exigir(set(metodos) == set(METODOS), 'Preflight/final exigem os seis métodos.')
        exigir((len(sorteios) == 1 and not args.instancias) if args.modo == 'preflight' else sorteios == sementes, 'Seleção de sementes/instâncias incompatível com o modo.')
    linhas = piloto if args.modo in ['calibration', 'pilot'] else final
    if args.instancias:
        exigir(len(set(args.instancias)) == len(args.instancias) and set(args.instancias) <= {r['identificador'] for r in linhas}, 'Instâncias fora do conjunto permitido.')
        linhas = [r for r in linhas if r['identificador'] in args.instancias]
    tarefas = []
    for r in linhas:
        caminho = (args.source / r['caminho']).resolve()
        exigir(caminho.is_relative_to(args.source.resolve()) and caminho.is_file(), f'Instância ausente/fora da origem: {caminho}')
        exigir(caminho.stem == r['identificador'] and identifica(caminho)[0] == r['familia'], 'Nome/família divergente do manifesto.')
        exigir(sha(caminho) == r['sha256'], f'Hash divergente: {caminho}')
        for metodo in metodos:
            for semente in sorteios:
                tarefas.append({'instancia': r['identificador'], 'familia': r['familia'], 'caminho_instancia': str(caminho),
                                'sha256_instancia': r['sha256'], 'metodo': metodo, 'semente': semente})
    return config, cpu, tarefas


def ambiente():
    saida = subprocess.check_output(['make', '-s', 'informacoes-build'], cwd=RAIZ, text=True)
    build = dict(l.split('=', 1) for l in saida.splitlines() if '=' in l)
    compilador = subprocess.check_output(shlex.split(build['CXX']) + ['--version'], text=True).strip()
    cpu = next((l.split(':', 1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')), platform.machine())
    ram = next(l.strip() for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemTotal:'))
    fontes = sorted(list((RAIZ / 'src').glob('*.cpp')) + list((RAIZ / 'include').glob('*.h')) + [RAIZ / 'Makefile'])
    conteudo = ''.join(str(p.relative_to(RAIZ))+':'+sha(p)+'\n' for p in fontes)
    assinatura = {'compilador': compilador, 'build': build, 'fontes': hashlib.sha256(conteudo.encode()).hexdigest()}
    carimbo = RAIZ / 'bin/protocolo-build.json'
    try:
        anterior = json.loads(carimbo.read_text()) if carimbo.is_file() else {}
        if not isinstance(anterior, dict):
            anterior = {}
    except (OSError, ValueError):
        anterior = {}
    executavel = RAIZ / 'bin/tp3'
    if anterior.get('assinatura') != assinatura or not executavel.is_file() or anterior.get('executavel_sha256') != sha(executavel):
        # Evita atribuir flags novas a objetos antigos compilados com outras opções.
        subprocess.run(['make', '-s', '-B', 'all'], cwd=RAIZ, check=True)
        json_atomico(carimbo, {'assinatura': assinatura, 'executavel_sha256': sha(executavel)})
    return {'compilador': compilador, 'build': build, 'kernel': platform.release(), 'sistema': platform.platform(),
            'cpu': cpu, 'ram': ram, 'python': platform.python_version(), 'executavel_sha256': sha(RAIZ / 'bin/tp3'),
            'fontes_sha256': hashlib.sha256(conteudo.encode()).hexdigest(),
            'orquestrador_sha256': sha(Path(__file__)), 'validador_sha256': sha(RAIZ / 'scripts/validar_execucao.py')}


def esperado(tarefa, config_path, cpu):
    return {k: tarefa[k] for k in ['instancia', 'familia', 'caminho_instancia', 'metodo', 'semente']} | {'config_arquivo': str(config_path), 'limite_cpu': format(cpu, '.17g')}


def conferir(pasta, tarefa, config_path, config, cpu, contrato_hash):
    recibo = json.loads((pasta / 'concluida.json').read_text())
    exigir(recibo['tarefa'] == tarefa and recibo['contrato_sha256'] == contrato_hash and recibo['codigo_saida'] == 0, 'Recibo incompatível.')
    exigir(sha(Path(tarefa['caminho_instancia'])) == tarefa['sha256_instancia'], 'Instância alterada.')
    for nome, digest in recibo['arquivos'].items():
        exigir(Path(nome).name == nome and sha(pasta / nome) == digest, 'Arquivo alterado/incompleto.')
    resultado_csv, solucao = validar(pasta, Path(tarefa['caminho_instancia']), esperado(tarefa, config_path, cpu), config)
    exigir(set(recibo['arquivos']) == {resultado_csv.name, solucao.name}, 'Recibo sem os dois artefatos obrigatórios.')


def executar(args):
    config, cpu, tarefas = planejar(args)
    if args.planejar:
        print(json.dumps({'modo': args.modo, 'cpu': cpu, 'config': config, 'execucoes': len(tarefas), 'tarefas': tarefas}, ensure_ascii=False, indent=2))
        return
    with exclusividade(RAIZ / 'results/.execucao.lock') as fd:
        env = ambiente()
        lote = args.saida.resolve() / args.modo / config['id']
        lote.mkdir(parents=True, exist_ok=True)
        contrato = {'versao': 1, 'modo': args.modo, 'cpu': cpu, 'config_sha256': sha(args.config), 'config': config,
                    'sementes_sha256': sha(RAIZ / 'config/sementes.txt'), 'ambiente': env, 'tarefas': tarefas,
                    'manifestos': {n: sha(RAIZ / f'instances/manifests/{n}.csv') for n in ['piloto', 'final']}}
        contrato_path = lote / 'contrato.json'
        config_path = lote / 'config.cfg'
        if contrato_path.exists():
            exigir(json.loads(contrato_path.read_text()) == contrato, 'Lote existente usa outro protocolo, configuração, código ou ambiente; escolha outro diretório.')
            exigir(sha(config_path) == contrato['config_sha256'], 'Cópia da configuração alterada.')
        else:
            exigir(not (lote / 'execucoes').exists(), 'Lote sem contrato contém resultados; use outro diretório.')
            config_path.write_bytes(args.config.read_bytes())
            json_atomico(lote / 'ambiente.json', {'data_utc': agora(), **env})
            json_atomico(contrato_path, contrato)
        contrato_hash = sha(contrato_path)
        for nome in ['execucoes', '.pendentes', 'invalidos']:
            (lote / nome).mkdir(exist_ok=True)
        puladas = 0
        for indice, tarefa in enumerate(tarefas, 1):
            chave = '__'.join(str(tarefa[k]) for k in ['instancia', 'metodo', 'semente'])
            destino = lote / 'execucoes' / chave
            if destino.exists():
                try:
                    conferir(destino, tarefa, config_path, config, cpu, contrato_hash)
                    puladas += 1
                    print(f'[{indice}/{len(tarefas)}] Válida, pulando: {chave}', flush=True)
                    continue
                except (ValueError, OSError, KeyError, TypeError, AttributeError, OverflowError, csv.Error) as erro:
                    destino.rename(lote / 'invalidos' / (chave + '__' + uuid.uuid4().hex))
                    print(f'Inválida, preservada para inspeção: {chave}: {erro}', flush=True)
            # Diretório temporário no mesmo filesystem: a renomeação publica o conjunto todo.
            pendente = Path(tempfile.mkdtemp(prefix=chave+'__', dir=lote / '.pendentes'))
            comando = [str(RAIZ / 'bin/tp3'), '--instancia', tarefa['caminho_instancia'], '--metodo', tarefa['metodo'],
                       '--config', str(config_path), '--semente', str(tarefa['semente']), '--cpu', format(cpu, '.17g'),
                       '--saida', str(pendente), '--salvar-solucao']
            inicio = agora()
            print(f'[{indice}/{len(tarefas)}] Executando: {chave}', flush=True)
            with (pendente / 'stdout.txt').open('w') as out, (pendente / 'stderr.txt').open('w') as err:
                codigo = processo(comando, fd, out, err)
            exigir(codigo == 0, f'Execução falhou (código {codigo}); arquivos preservados em {pendente}.')
            exigir(sha(RAIZ / 'bin/tp3') == env['executavel_sha256'] and sha(config_path) == contrato['config_sha256'], 'Executável/configuração mudou durante o lote.')
            exigir(sha(Path(tarefa['caminho_instancia'])) == tarefa['sha256_instancia'], 'Instância mudou durante a execução.')
            resultado_csv, solucao = validar(pendente, Path(tarefa['caminho_instancia']), esperado(tarefa, config_path, cpu), config)
            json_atomico(pendente / 'concluida.json', {'versao': 1, 'tarefa': tarefa, 'contrato_sha256': contrato_hash,
                         'inicio_utc': inicio, 'fim_utc': agora(), 'codigo_saida': codigo, 'comando': comando,
                         'arquivos': {p.name: sha(p) for p in [resultado_csv, solucao]}})
            pendente.rename(destino)
        print(f'Lote completo: {len(tarefas)} válidas; {puladas} puladas; {len(tarefas)-puladas} executadas. {lote}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modo', required=True, choices=['calibration', 'pilot', 'preflight', 'final'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--saida', type=Path, default=RAIZ / 'results')
    parser.add_argument('--source', type=Path, default=RAIZ / 'instances/source')
    parser.add_argument('--instancias', nargs='+')
    parser.add_argument('--metodos', nargs='+', choices=METODOS)
    parser.add_argument('--sementes', nargs='+', type=int)
    parser.add_argument('--cpu', type=float)
    parser.add_argument('--planejar', action='store_true', help='Valida e mostra o plano, sem compilar nem executar métodos.')
    args = parser.parse_args()
    args.config = args.config.resolve()
    args.source = args.source.resolve()
    try:
        executar(args)
    except KeyboardInterrupt:
        print('Interrompido; resultados concluídos preservados. Repita o mesmo comando para retomar.', file=sys.stderr)
        return 130
    except (ValueError, OSError, KeyError, TypeError, AttributeError, OverflowError, subprocess.SubprocessError, csv.Error) as erro:
        print(f'Erro: {erro}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
