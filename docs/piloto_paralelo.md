# Piloto paralelo exploratório (inicial gulosa e aleatória)

Na raiz:

```bash
python3 scripts/piloto_paralelo.py --embaralhar 42 --planejar   # confere, sem executar
python3 scripts/piloto_paralelo.py --embaralhar 42              # executa / retoma
```

Matriz do piloto (10 instâncias de `instances/manifests/piloto.csv` × Hbase, Hext,
Hint, Hcomb × sementes 1001–1010 = 400 execuções), rodada duas vezes: partindo da
construção gulosa (padrão do executável) e da inicial aleatória da RLS-f7
(`--inicial aleatoria`, mesma semente). Total de 800 execuções de até 60 s de
CPU; com 6 núcleos físicos, teto nominal de ~134 min de parede (`--max-minutos`
altera o teto da chamada; padrão: nominal + 30 min).

Os dois lotes rodam em sequência (gulosa, depois aleatória), cada um com contrato,
validação completa de cada solução, recibos, retomada auditada, trava global,
núcleos físicos fixos e ordem sorteada. Saídas:

- `results/piloto_paralelo_s10_j6/gulosa/congelada_v2/`
- `results/piloto_paralelo_s10_j6/aleatoria/congelada_v2/`

cada uma com `tabela_comparacao.csv` e `integridade.json` ao concluir.

Progresso: o console mostra `[início]` e `[ok]` por execução, com a barra
`concluídas/400` do lote corrente. Para acompanhar em outro terminal:
`ls results/piloto_paralelo_s10_j6/*/congelada_v2/execucoes | wc -l`.

Retomada: Ctrl+C (código 130) ou teto atingido (124) preservam os completos;
repita exatamente o mesmo comando. Lotes já completos são apenas reauditados.
Durante o lote, não altere `scripts/piloto_paralelo.py`,
`scripts/benchmark_reduzido_paralelo.py` nem o C++, e não rode `make`: o
contrato recusaria a retomada. Opções úteis: `--iniciais aleatoria` roda só uma
variante; `--sementes N` usa as N primeiras sementes (muda o diretório de saída).

Exploratório: NÃO seleciona nem grava H* e não substitui `scripts/piloto.py`.
