"""Confere um CSV individual e sua solução antes de publicar ou retomar."""

import csv
import math
from pathlib import Path


def exigir(condicao, mensagem):
    if not condicao:
        raise ValueError(mensagem)


def linha_csv(caminho):
    with caminho.open(encoding='utf-8', newline='') as f:
        leitor = csv.DictReader(f, strict=True)
        linhas = list(leitor)
        exigir(leitor.fieldnames and len(set(leitor.fieldnames)) == len(leitor.fieldnames), 'Cabeçalho inválido.')
    exigir(len(linhas) == 1 and None not in linhas[0] and None not in linhas[0].values(), 'CSV incompleto ou com registros excedentes.')
    return linhas[0]


def validar(pasta, instancia, esperado, config):
    resultados = [p for p in pasta.glob('*.csv') if not p.name.endswith('.solucao.csv')]
    exigir(len(resultados) == 1, 'Esperado um CSV de resultado.')
    r = linha_csv(resultados[0])
    for chave, valor in esperado.items():
        exigir(r.get(chave) == str(valor), f'Identificação divergente: {chave}.')
    for chave in ['chapas_perturbadas', 'max_reinicios', 'max_avaliacoes_reparo', 'rls_max_avaliacoes']:
        exigir(r.get(chave) == config[chave], f'Parâmetro divergente: {chave}.')
    exigir(r['config_id'] == config['id'] and r['config_estado'] == config['estado'] and r['versao'] == '1' and r['validada'] == '1', 'Versão/configuração/validação inválida.')
    k, lb = int(r['K']), int(r['LBref'])
    exigir(0 < lb <= k and lb == max(int(r['LBarea']), int(r['LBdmv'])), 'Limites inconsistentes.')
    desvio = lambda n: 100*(n-lb)/lb
    exigir(math.isclose(float(r['desvio']), desvio(k), abs_tol=1e-10), 'Desvio inconsistente.')
    total, melhor, cpu = map(float, (r['tempo_total'], r['tempo_melhor'], r['limite_cpu']))
    exigir(all(math.isfinite(x) for x in [total, melhor, cpu]) and 0 <= melhor <= total and cpu > 0, 'Tempo inválido.')
    exigir(r['alcancou_lb'] == str(int(k == lb)) and r['limite_cpu_atingido'] == str(int(total >= cpu)), 'Indicadores inconsistentes.')
    metodo = r['metodo']
    rls = metodo == 'RLS-f7'
    exigir(r['controle_auxiliar'] == str(int(metodo == 'Haleat')), 'Controle auxiliar incorreto.')
    parada = r['motivo_parada']
    exigir(parada in ['limite_inferior', 'limite_cpu', 'limite_avaliacoes' if rls else 'orcamento_reparo'], 'Parada inválida.')
    exigir((parada == 'limite_inferior') == (k == lb) and (parada != 'limite_cpu' or total >= cpu), 'Parada inconsistente.')
    exigir(r['unidade_avaliacoes'] == ('f7' if rls else 'candidato_externo'), 'Unidade de avaliações incorreta.')
    exigir(int(r['avaliacoes']) >= (1 if rls else 0), 'Avaliações inválidas.')
    if rls:
        exigir(int(r['avaliacoes']) <= int(config['rls_max_avaliacoes']), 'Teto de avaliações excedido.')
    else:
        exigir(int(r['avaliacoes']) <= int(config['max_avaliacoes_reparo'])*int(r['tentativas_reducao']), 'Orçamento de reparo excedido.')
    for campos, aplicavel in [(['historico_atualizacoes', 'historico_reinicios', 'movimentos_orientados', 'melhorias_orientadas'], metodo in ['Hext', 'Hcomb']),
                              (['ativacoes_internas', 'decodificacoes_extras', 'melhorias_internas', 'empacotamentos_completos'], metodo in ['Hint', 'Hcomb', 'Haleat']),
                              (['f7', 'area_perfil', 'trocas', 'inversoes', 'aceitos_rls', 'melhorias_rls'], rls)]:
        for campo in campos:
            exigir(int(r[campo]) >= 0 if aplicavel else r[campo] == '', f'Métrica inaplicável/inválida: {campo}.')
    if metodo in ['Hint', 'Hcomb', 'Haleat']:
        exigir(int(r['decodificacoes_extras']) <= 16*int(r['ativacoes_internas']), 'Teto interno excedido.')
    anterior, disponivel = None, False
    for t in ['0_1', '1', '5', '10', '30', '60']:
        a, b = r['K_'+t], r['desvio_'+t]
        exigir(bool(a) == bool(b) and (bool(a) or not disponivel), 'Marco parcial ou disponibilidade decrescente.')
        if a:
            n = int(a)
            exigir(n >= k and (anterior is None or n <= anterior) and math.isclose(float(b), desvio(n), abs_tol=1e-10), 'Evolução inconsistente.')
            anterior, disponivel = n, True
    # A solução é sempre conservada para que a retomada confira a geometria novamente.
    nome = r['solucao_arquivo']
    exigir(nome and Path(nome).name == nome, 'Nome de solução inválido.')
    solucao = pasta / nome
    linhas = [l.split() for l in instancia.read_text().splitlines() if l.strip()]
    w, h = map(int, linhas[1])
    copias = {}
    for l in linhas[2:]:
        tipo, largura, altura, demanda = map(int, l[:4])
        for _ in range(demanda):
            copias[len(copias)+1] = tipo, largura, altura
    with solucao.open(newline='') as f:
        pecas = list(csv.DictReader(f, strict=True))
    exigir(len(pecas) == len(copias), 'Demanda incompleta.')
    vistas, chapas = set(), {}
    for linha in pecas:
        p = {c: int(v) for c, v in linha.items()}
        id_peca = p['copia_id']
        exigir(p['versao'] == 1 and id_peca in copias and id_peca not in vistas, 'Cópia ausente, desconhecida ou repetida.')
        vistas.add(id_peca)
        tipo, largura, altura = copias[id_peca]
        exigir(p['rotacionada'] in [0, 1] and p['tipo_id'] == tipo, 'Tipo/orientação inválido.')
        if p['rotacionada']:
            largura, altura = altura, largura
        exigir((p['largura'], p['altura']) == (largura, altura) and 0 <= p['x'] <= w-largura and 0 <= p['y'] <= h-altura, 'Dimensões/contenção inválidas.')
        chapas.setdefault(p['chapa'], []).append(p)
    exigir(set(chapas) == set(range(k)), 'Número de chapas divergente.')
    for itens in chapas.values():
        for j, a in enumerate(itens):
            for b in itens[j+1:]:
                exigir(not (a['x'] < b['x']+b['largura'] and b['x'] < a['x']+a['largura'] and a['y'] < b['y']+b['altura'] and b['y'] < a['y']+a['altura']), 'Sobreposição.')
    if rls:
        ultima = chapas[k-1]
        bordas = sorted({0, w} | {p['x'] for p in ultima} | {p['x']+p['largura'] for p in ultima})
        perfil = sum((b-a)*max([p['y']+p['altura'] for p in ultima if p['x'] <= a < p['x']+p['largura']], default=0) for a, b in zip(bordas, bordas[1:]))
        exigir(perfil == int(r['area_perfil']) and w*h*(k-1)+perfil == int(r['f7']), 'Perfil/f7 divergente.')
    return resultados[0], solucao
