"""Confere o selo de parâmetros antes de usar a configuração nas próximas etapas."""

import json
from pathlib import Path

from executar_experimentos import RAIZ, sha
from validar_execucao import exigir


def verificar(config=None, selo=None, sementes=None):
    config = config or RAIZ / 'config/congelada_v1.cfg'
    selo = selo or config.with_suffix('.json')
    sementes = sementes or RAIZ / 'config/sementes.txt'
    dados = json.loads(selo.read_text())
    exigir(dados['config_sha256'] == sha(config), 'Configuração congelada foi alterada.')
    exigir(dados['sementes_sha256'] == sha(sementes), 'Sementes comuns foram alteradas.')
    exigir(dados['plano_sha256'] == sha(RAIZ / 'docs/calibracao.md'), 'Plano de calibração foi alterado.')
    exigir(dados['execucoes_validas'] == 160, 'Congelamento sem calibração completa.')
    return dados


if __name__ == '__main__':
    verificar()
    print('Configuração congelada e sementes: SHA-256 conferidos.')
