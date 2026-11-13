# Corte de Estoque Bidimensional

Projeto de Heurísticas e Metaheurísticas da UFMG para minimizar o número de
chapas retangulares usadas para atender às demandas de peças, permitindo
rotação de 90 graus e empacotamento livre, sem sobreposição.

## Preparação

Requer Linux, Python 3.9+ e GCC com C++20/GNU Make. No Mint/Ubuntu:

```bash
sudo apt install build-essential python3
```

Depois de clonar, entre na pasta do repositório e execute todos os comandos
abaixo **na raiz do projeto**. Copie as instâncias originais fornecidas pelo
grupo para `instances/source/`, preservando as mesmas subpastas e nomes dos
manifestos em `instances/manifests/`. As instâncias não acompanham o Git: peça
essa pasta a quem já a possui. Não é preciso instalar bibliotecas Python extras.

```bash
make
python3 scripts/verificar_congelamento.py
```

Parâmetros comuns: `config/congelada_v2.cfg`, duas chapas perturbadas,
1.000.000 avaliações de reparo e 50.000 reinícios por tentativa. Não edite essa
configuração nem as sementes. Cada execução tem até 60 segundos de CPU.

## Quatro formas de executar

| Experimento | Comando | Matriz | Teto nominal de CPU |
|---|---|---|---|
| Piloto reduzido (TA) | `python3 scripts/piloto_v1.py` | 5 instâncias × 4 propostas × 3 sementes = 60 | 1 hora |
| Piloto completo | `python3 scripts/piloto.py --max-minutos 420` | 10 instâncias × 4 propostas × 10 sementes = 400 | 6h40 |
| Benchmark reduzido (TA) | `python3 scripts/benchmark_reduzido.py` | 6 instâncias × 6 métodos × 3 sementes = 108 | 1h48 |
| Benchmark completo | `python3 scripts/benchmark.py` | 153 instâncias × 6 métodos × 10 sementes = 9180 | 153 horas |

Os tetos são de CPU, além de compilação e auditoria; paradas antecipadas podem
reduzir bastante o tempo. Piloto reduzido limita a chamada a 75 minutos de
parede; benchmark reduzido a 120. Use `--max-minutos N` para definir quanto tempo
reservar à chamada. O benchmark completo não tem teto total por padrão.

Todos têm progresso e retomada. Para interromper, use Ctrl+C; repita exatamente
o mesmo comando para continuar. Resultados completos são conferidos e pulados;
a execução interrompida é refeita. Teto total atingido retorna 124. Mantenha a
máquina na tomada e sem suspensão. Rode um lote por vez em cada computador.

Acrescente `--planejar` para conferir sem executar ou `--analisar` para auditar
dados completos e gerar os resumos sem repetir os algoritmos.

O piloto reduzido já concluído é preservado nos blocos `results/ta_v1/` e
`results/ta_v1_extra/`. Para gerar sua tabela geral sem repetir as 60 execuções:

```bash
python3 scripts/piloto_v1.py --analisar
```

O benchmark reduzido é independente dos pilotos e **não exige H***. Ele usa
Hbase, Hext, Hint, Hcomb, Haleat (controle auxiliar) e RLS-f7, nas instâncias
finais A36, A32, BENG03, BENG05, CLASS 3/100/01 e CLASS 7/100/01. São resultados
preliminares descritivos, sem substituir a avaliação completa do TP3.

O benchmark completo mantém a exigência do piloto completo, que grava
`config/h_estrela_v2.json`. Isso preserva a escolha antecipada para a hipótese
de comparação com a literatura; a tabela geral continua incluindo os seis métodos.
Se outra pessoa rodar o completo, envie também o selo de H* e o diretório
`results/pilot/congelada_v2/` produzidos pelo piloto correspondente.

## Resultados e trabalho em grupo

Cada execução salva CSV, solução geométrica, recibo e logs automaticamente.
As tabelas gerais ficam em:

- Piloto reduzido: `results/ta_v1/tabela_comparacao.csv` (quatro métodos).
- Piloto completo: `results/pilot/resumo.csv` (quatro métodos e seleção de H*).
- Benchmark reduzido: `results/benchmark_reduzido/congelada_v2/tabela_comparacao.csv`.
- Benchmark completo: `results/final/congelada_v2/tabela_comparacao.csv`.

As tabelas dos benchmarks têm uma linha por método: K médio, desvio médio e
mediano para LBref, percentual de alcance de LBref, mediana do tempo até melhor
K, CPU média e motivos de parada. Valores menores de K/desvio são melhores.
Cada instância tem o mesmo número de sementes. A tabela é descritiva e não
substitui a análise estatística das hipóteses do TP3. No reduzido, as três
famílias têm peso igual; não extrapole sua média para o conjunto completo.

Resultados de pilotos são versionáveis. Benchmarks permanecem ignorados pelo
Git por padrão: compartilhe a pasta completa por arquivo compactado/drive e
faça backup. A conclusão só é anunciada após validar toda a matriz e as soluções.

## Organização e testes

`src/` e `include/`: C++; `scripts/` e `config/`: execução; `tests/`: testes;
`instances/`: dados e manifestos; `results/`: saídas; `docs/`: documentação;
`bin/` e `obj/`: compilação. Materiais e prompts locais são ignorados pelo Git.

```bash
make test
make integration-test
make orchestration-test
```

Para uma execução individual: `./bin/tp3 --ajuda`.
Detalhes: [execução](docs/execucao.md), [piloto](docs/piloto.md),
[piloto reduzido](docs/piloto_v1.md), [benchmark reduzido](docs/benchmark_reduzido.md)
e [benchmark completo](docs/benchmark.md).
