# Benchmark estendido

Comando: `python3 scripts/benchmark_estendido.py -j 6 --embaralhar 42`.
Somente planejar: acrescente `--planejar`. Somente reauditar e refazer a tabela:
acrescente `--analisar` ao mesmo comando.

Instâncias: as 18 de `config/benchmark_estendido.txt`, todas do manifesto final e
nenhuma do piloto (A4, A10, A28, A32, A18, A9, BENG01, BENG02, BENG04, BENG08,
BENG09, BENG10, cl_01_020_01, cl_03_020_01, cl_05_060_01, cl_07_060_01,
cl_08_100_01, cl_10_100_01). A32 também integra o benchmark reduzido. A seleção
foi feita pelo grupo; registre o critério no TE.

Seis métodos e, por padrão, três sementes comuns (1001–1003): 324 execuções de até
60 s de CPU. `--sementes N` usa as N primeiras sementes comuns (10 → 1080
execuções). Com `-j 6`, o teto nominal é ~54 min de parede; `--max-minutos`
altera o teto da chamada (padrão: nominal + 30 min), nunca os 60 s por execução.

Mesmas garantias do benchmark reduzido paralelo: contrato com lista, sementes,
processos, ordem e hashes do executável/ambiente; validação completa de cada
solução; recibos; retomada auditada; trava global herdada por todos os filhos.
Saída em `results/benchmark_estendido_s<N>_j<J>/congelada_v2/`, com
`tabela_comparacao.csv` e `integridade.json`. Lotes com lista, sementes, -j ou
executável diferentes não se misturam.

Cada processo C++ fica fixo num núcleo físico distinto (uma CPU lógica por núcleo,
sem usar os dois threads SMT do mesmo núcleo); as execuções saem de uma fila única,
sorteada por --embaralhar, e cada uma ocupa o núcleo que vagar. A lista de CPUs
entra no contrato e cada recibo registra a CPU usada. -j não pode exceder o
número de núcleos físicos (padrão: todos).

O limite de 60 s é de CPU, mas processos simultâneos disputam cache e memória:
relate o -j usado e não use mais processos que núcleos físicos.
