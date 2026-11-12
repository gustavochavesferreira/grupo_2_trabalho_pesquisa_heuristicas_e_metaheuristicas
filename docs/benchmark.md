# Benchmark final em um comando

Na raiz do repositório, na máquina escolhida para o benchmark real:

```bash
python3 scripts/benchmark.py
```

Requer Linux, Python 3.9+, Make e GCC C++20, as instâncias originais em
instances/source/, os manifestos, a configuração congelada e o selo/contrato
do piloto. Em outra máquina, copie esses artefatos e as instâncias também.
O ambiente real será registrado automaticamente, e a compilação ocorre quando
necessária. Use a mesma máquina e ambiente durante todo o lote.

O comando cobre as Tarefas 24, 25 e 26 em um único lote, na ordem do manifesto
final: 38 A (2280 execuções), dez BENG (600) e 105 CLASS (6300). São seis métodos,
dez sementes e até 60 segundos de CPU por execução, sempre sequenciais. A barra
mostra concluídas/9180 e porcentagem, avançando entre execuções. Na retomada,
resultados existentes são auditados e contam no progresso quando conferidos.

Resultados são salvos automaticamente em results/final/congelada_v1/execucoes/:
CSV, solução geométrica, recibo e logs por execução. Contrato, configuração e
ambiente ficam no diretório do lote. Ao final, uma auditoria independente dos
arquivos exportados gera integridade_familias.json nesse mesmo diretório.
Esse relatório confere as matrizes por família, sem realizar a análise
estatística das Tarefas 27 e 28.

Mantenha o terminal aberto, desative a suspensão e deixe a máquina ligada à
tomada. Não execute outros lotes dos algoritmos em paralelo. O teto nominal é
153 horas de CPU (6 dias e 9 horas), mais preparação/auditoria; paradas por
limite inferior ou orçamento de reparo podem encurtar bastante esse tempo.

Para interromper, use Ctrl+C. Para retomar, execute exatamente o mesmo comando.
Não apague resultados, altere parâmetros, código ou ambiente durante o lote.
Uma falha preserva os resultados completos e os logs para diagnóstico.

Para conferir somente o planejamento, sem iniciar o benchmark:

```bash
python3 scripts/benchmark.py --planejar
```

Os resultados finais permanecem ignorados pelo Git por padrão, conforme a regra
geral de results/. Faça cópia de segurança do diretório completo. Para versionar
explicitamente ao terminar, revise o tamanho dos dados e use git add -f somente
em results/final/congelada_v1/execucoes/, contrato.json, ambiente.json,
config.cfg e integridade_familias.json; não inclua .pendentes/ ou invalidos/.

Preparar o comando não significa executar as Tarefas 24 a 26. Elas estarão
concluídas somente após a execução e a auditoria das 9180 soluções.
