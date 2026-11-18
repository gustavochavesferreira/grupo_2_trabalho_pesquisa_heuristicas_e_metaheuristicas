"""Retoma o benchmark completo paralelo após reinício da máquina.

Após um reboot, o kernel pode informar um MemTotal alguns kB diferente (memória
reservada no boot varia), e o contrato recusaria a retomada. Este lançador aceita
SOMENTE essa diferença (todos os demais campos do ambiente — executável, fontes,
compilador, kernel, CPU, scripts — continuam exigidos idênticos) e só se a variação
for menor que 0,01% da RAM. A tolerância é registrada em <lote>/retomadas.json.

Não altera o contrato, os recibos nem benchmark_completo_paralelo.py. Uso: os
mesmos argumentos do benchmark_completo_paralelo.py, por exemplo
    python3 scripts/retomar_benchmark_completo_paralelo.py --embaralhar 42
"""

import argparse
import json
import re
import sys

import benchmark_completo_paralelo as bc
import benchmark_reduzido_paralelo as par
from executar_experimentos import agora, json_atomico

TOLERANCIA = 1e-4


def kb(ram):
    return int(re.search(r'(\d+)\s*kB', ram)[1])


def ambiente_tolerante(contrato_path, registro):
    original = par.ambiente

    def ambiente():
        atual = original()
        if not contrato_path.exists():
            return atual
        salvo = json.loads(contrato_path.read_text())['ambiente']
        diferentes = {k for k in atual.keys() | salvo.keys() if atual.get(k) != salvo.get(k)}
        if diferentes == {'ram'} and abs(kb(atual['ram'])-kb(salvo['ram'])) <= TOLERANCIA*kb(salvo['ram']):
            historico = json.loads(registro.read_text()) if registro.exists() else []
            historico.append({'data_utc': agora(), 'motivo': 'MemTotal difere após reinício da máquina',
                              'ram_contrato': salvo['ram'], 'ram_atual': atual['ram']})
            json_atomico(registro, historico)
            print(f"Aviso: MemTotal {kb(atual['ram'])} kB difere do contrato ({kb(salvo['ram'])} kB); "
                  f'diferença tolerada e registrada em {registro}.', flush=True)
            return {**atual, 'ram': salvo['ram']}
        return atual
    return ambiente


def main():
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument('-j', '--jobs', type=int, default=len(par.nucleos_fisicos()))
    pre.add_argument('--inicial', choices=bc.INICIAIS, default='aleatoria')
    a, _ = pre.parse_known_args()
    saida = bc.saida_padrao(a.jobs, a.inicial)
    par.ambiente = ambiente_tolerante(saida/'contrato.json', saida/'retomadas.json')
    return bc.main()


if __name__ == '__main__':
    sys.exit(main())
