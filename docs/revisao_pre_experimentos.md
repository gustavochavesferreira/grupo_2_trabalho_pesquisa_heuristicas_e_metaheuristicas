# Revisão antes dos experimentos

A infraestrutura está pronta para iniciar a calibração da Tarefa 21. Os
parâmetros continuam provisórios. Não foram executados calibração, piloto ou
benchmark científicos. A aprovação técnica desta revisão não substitui a grade,
o critério de escolha, o congelamento dos parâmetros e a seleção de H*.

## Código e organização

Os seis métodos, decodificadores, geometria, limites inferiores, cronômetro e
verificador independente são C++20, compilados por GCC com -O2 e avisos
habilitados. Python prepara listas, coordena processos e audita arquivos depois
da execução; não executa busca, movimentos ou decodificação dentro do orçamento
cronometrado. A estrutura src/include/tests/scripts/config é mantida.

O estilo foi confrontado com codigo_exemplo: estruturas e funções simples,
using namespace std, nomes descritivos e comentários em português. Referências
preservam estruturas grandes ou permitem modificá-las; transferências por move
foram usadas nos estados grandes que já não são necessários no local anterior.
Não foi feita uma reescrita cosmética dos algoritmos ou adotada uma nova variante.

Correções e melhorias:

- Hbase verifica CPU após validar uma redução e antes de aceitá-la.
- A inserção inferior-esquerda usa a mesma grade/ordem de cantos, mas a percorre
  sem materializar todos os candidatos e para na primeira posição admissível.
- IBL/perfil consultam CPU em blocos de até 64 obstáculos, preservando as
  verificações externas e a interrupção cooperativa.
- Foram evitadas cópias de estados/empacotamentos e composições recalculadas.
- A retomada exige esquema CSV completo, cabeçalho de solução e coerência dos
  marcos após o término. O rebuild recupera carimbo auxiliar inválido.
- Uma execução nova é auditada geometricamente uma vez, antes da publicação;
  execuções retomadas continuam sendo auditadas novamente.

Permanecem as oito tentativas básicas, teto interno de 16, amostras, desempates,
operadores, histórico, aceitação e semente explícita. Limites inferiores não foram
substituídos por aproximações mais baratas e validações não foram desativadas.

## Verificação

Comandos da suíte:

```bash
make -j2 test catalog-test
make integration-test
make orchestration-test
```

Também foram compilados todos os módulos com GCC C++20, -O0 -g,
-fsanitize=address,undefined e -fno-sanitize-recover=all, executando os testes
ibl, empacotador_base, vnd, hbase e integracao. Passaram sem diagnóstico de
acesso inválido ou comportamento indefinido. LeakSanitizer não está disponível
sob o mecanismo de execução com ptrace deste ambiente; a execução de ASan usou
ASAN_OPTIONS=detect_leaks=0. Não se afirma cobertura de detecção de vazamentos.

As regressões incluem o prazo na aceitação de Hbase, cabeçalho incompleto e
marco incompatível com término. Os oráculos existentes continuam protegendo
geometria, seleção de posições, conservação e aritmética extrema.

Doze execuções adicionais de revisão cobriram os seis métodos em A14 (809
cópias) e cl_09_060_02 (60 cópias), ambas do piloto. Usaram semente 1001, CPU de
2 segundos, até 40 candidatos externos e 200 avaliações da RLS, com solução
exportada e auditada. Todos produziram soluções válidas. Saídas foram temporárias
para não serem confundidas com resultados científicos.

## Medição local de desempenho

Uma comparação da versão anterior com a revisada usou semente 1001 e o mesmo
orçamento de operações. Em Hbase, reparo desligado para medir a construção;
na RLS, 200 avaliações. CPU máxima de 3 segundos, sem corte temporal nos casos
medidos. Os CSVs de solução, K e avaliações foram idênticos em cada par.

| Instância | Método | CPU anterior (s) | CPU revisada (s) |
|---|---|---:|---:|
| BENG01 | construção Hbase | 0,000684 | 0,000338 |
| BENG10 | construção Hbase | 0,093276 | 0,077443 |
| A14 | construção Hbase | 1,100537 | 0,819539 |
| BENG01 | RLS-f7 | 0,043574 | 0,022192 |
| BENG10 | RLS-f7 | 1,627900 | 0,230978 |
| A14 | RLS-f7 | 2,463335 | 0,822294 |

São observações locais de desempenho, sem repetições estatísticas: não estimam
vantagem científica entre métodos nem garantem o mesmo ganho em toda instância.
Não foram usadas para escolher parâmetros ou H*. Melhor desempenho pode
permitir mais avaliações sob o mesmo limite de CPU, como esperado.

## Limpeza e próximo passo

Caches Python gerados pela revisão foram removidos. Executáveis e objetos de
compilação foram mantidos para uso imediato. Não foram removidos PDFs, materiais,
instâncias, manifestos, resultados ou arquivos fornecidos pelo usuário.
O arquivo PROMPT_MESTRE.md existente foi preservado; não é dependência de execução.

O próximo passo é definir a grade e o critério de calibração, usar somente as
10 instâncias-piloto, escolher uma configuração comum e congelá-la. Só depois
cabem piloto formal, seleção de H* e pré-execução da matriz final. Um limite
curto de revisão não é garantia de tempo suficiente para construir a inicial
em qualquer instância; os experimentos devem usar seus orçamentos previstos.
