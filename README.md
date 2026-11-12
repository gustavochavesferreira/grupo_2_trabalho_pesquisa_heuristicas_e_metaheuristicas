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
./bin/tp3
```

Neste estágio, o executável apenas apresenta o projeto; as heurísticas ainda
não estão implementadas.

Para executar os testes e limpar os artefatos de compilação:

```bash
make test
make clean
```
