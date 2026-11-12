# TP3 — Corte de Estoque Bidimensional

Projeto da disciplina de Heurísticas e Metaheurísticas da UFMG para desenvolver
e avaliar heurísticas que minimizam o número de chapas retangulares necessárias
para atender às demandas de peças, permitindo rotação de 90 graus e sem
sobreposição.

## Organização

- `src/` e `include/`: código C++ e cabeçalhos.
- `tests/`: testes.
- `scripts/` e `config/`: scripts e configurações.
- `instances/source/`: instâncias fornecidas manualmente, fora do Git.
- `results/`: resultados gerados.
- `docs/`: decisões de implementação.
- `materiais_uteis_para_consulta/`: TP3 e materiais de referência.
- `bin/` e `obj/`: executáveis e objetos gerados pela compilação.

## Compilar e executar

Requer GNU Make e GCC (`g++`) com suporte a C++20. Na raiz do repositório:

```bash
make
./bin/tp3 --ajuda
./bin/tp3 --instancia tests/data/valida.txt --metodo Hcomb \
  --config config/provisoria.cfg --semente 1001 --cpu 1 \
  --saida results/teste --salvar-solucao
```

Troque o caminho pela instância fornecida manualmente. Métodos: `Hbase`, `Hext`,
`Hint`, `Hcomb`, `Haleat` (controle auxiliar) e `RLS-f7`. O limite é de CPU em
segundos. Cada execução gera um CSV validado; salvar a solução é opcional.
A configuração de exemplo é provisória, ainda sem calibração ou congelamento.
Argumentos, configuração e campos do CSV: [docs/execucao.md](docs/execucao.md).

Para executar os testes e limpar os artefatos de compilação:

```bash
make test
make integration-test
make clean
```

## Limites inferiores

O projeto usa o limite por área e o limite para rotação de Dell'Amico, Martello e
Vigo, *A lower bound for the non-oriented two-dimensional bin packing problem*,
Discrete Applied Mathematics, 118:13–24, 2002 (equação 8, após CUTSQ).
`LBref` é o maior dos dois. Fórmulas, cuidados e testes estão em
[docs/limites_inferiores.md](docs/limites_inferiores.md).
