# Benchmark completo paralelo (H* do piloto paralelo)

Na raiz:

```bash
python3 scripts/benchmark_completo_paralelo.py --embaralhar 42 --planejar   # audita o piloto, mostra H* e o plano
python3 scripts/benchmark_completo_paralelo.py --embaralhar 42              # executa / retoma
```

Matriz igual à do `benchmark.py`: 153 instâncias finais × Hbase, Hext, Hint, Hcomb,
Haleat, RLS-f7 × sementes 1001–1010 = 9180 execuções de até 60 s de CPU
(A 2280, BENG 600, CLASS 6300). Com 6 núcleos físicos, o teto nominal é de ~25,5 h
de parede; execuções que atingem o LBref terminam antes. Sem teto por padrão;
`--max-minutos N` limita a chamada.

## Solução inicial (`--inicial`, padrão `aleatoria`)

A partida é a mesma para todos os métodos, inclusive a RLS-f7:

- `aleatoria`: as propostas e o Haleat partem da inicial aleatória da RLS-f7
  (`--inicial aleatoria`, mesma semente). A RLS-f7 é a versão publicada.
- `gulosa`: as propostas e o Haleat partem da construção gulosa. A RLS-f7 recebe
  `--inicial gulosa`, uma variante diagnóstica que não é a RLS-f7 publicada:
  - a solução gulosa entra como incumbente, e a RLS só devolve outra se o f7 dela
    for menor;
  - a busca parte de uma permutação induzida pela gulosa. Para cada chapa,
    procura-se uma ordem e uma orientação das peças que o IBL empacote numa chapa
    só: até 1000 tentativas por chapa, todas contadas como avaliações.
  - O IBL (next-fit) nem sempre reproduz o layout best-fit da gulosa. Nas 153
    instâncias finais, a permutação induzida começa com o mesmo K em 98 e com
    1 a 5 chapas a mais em 55. Por isso a gulosa é mantida como incumbente.

O argumento é definido por tarefa e fica registrado no contrato e em cada recibo.

## H*

H* vem do lote do piloto paralelo com a **mesma** inicial
(`results/piloto_paralelo_s10_j6/<inicial>/congelada_v2`, aceito pelo grupo como
piloto válido). A cada chamada, as 400 execuções desse lote são reauditadas
(contrato, recibos, soluções e o `--inicial` de cada comando). A escolha segue a
regra do `piloto.py`: menor desvio médio exato, depois maior alcance do LBref,
depois menor mediana do tempo até o melhor K. A escolha e o hash do contrato do
piloto entram no contrato do benchmark: se o piloto mudar, a retomada é recusada.
Com os lotes atuais, H* = Hbase nas duas iniciais.

Este script não grava `config/h_estrela_v2.json`. O caminho sequencial oficial
(`piloto.py` seguido de `benchmark.py`) continua independente.

## Saídas

`results/benchmark_completo_paralelo_j6/<inicial>/congelada_v2/`:

- `execucoes/`: CSV, solução, recibo e logs de cada execução;
- `tabela_comparacao.csv`: resumo por método;
- `integridade.json`: confirma que o lote está completo e válido;
- `h_estrela.json`: escolha de H* e resumo do piloto;
- `comparacoes_h_estrela.csv`: H* contra cada outro método, pareado por
  (instância, semente) pelo K: vitórias, empates, derrotas e p do teste dos sinais
  exato bilateral, sem correção de multiplicidade.

## Retomada

Mesmas garantias do benchmark estendido: trava global, núcleos físicos fixos,
ordem sorteada e validação completa de cada solução. Ctrl+C (código 130) ou teto
atingido (124) preservam as execuções completas; repita exatamente o mesmo comando.
Durante o lote, não altere os scripts nem o C++, e não rode `make`: o contrato
recusaria a retomada.
