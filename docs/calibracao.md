# Calibração da Tarefa 21 — plano definido antes das execuções

Usar somente as dez instâncias do manifesto piloto e Hbase, Hext, Hint, Hcomb.
Grade pequena em torno dos valores provisórios, variando um fator por vez:

| Opção | Chapas perturbadas | Reinícios | Candidatos de reparo |
|---|---:|---:|---:|
| base | 2 | 5 | 1000 |
| chapas3 | 3 | 5 | 1000 |
| reinicios10 | 2 | 10 | 1000 |
| reparo2000 | 2 | 5 | 2000 |

A grade verifica um aumento moderado de diversificação e dois aumentos de
esforço, sem uma busca cartesiana grande. Não identifica interações entre fatores.
São 160 execuções: 4 opções x 4 métodos x 10 instâncias, com semente comum 1001 e
3 segundos de CPU, contra 60 segundos e dez sementes do piloto formal. Esse
orçamento admite a construção inicial do maior caso nas verificações anteriores.
Uma semente reduz custo e sobreajuste da escolha; limita a precisão da calibração.
Não são estimados efeitos científicos ou escolhido H* nesta etapa.

Critério lexicográfico fixado previamente, agregando igualmente as 40 execuções
de cada opção: menor desvio médio para LBref; maior proporção de alcance de
LBref; menor mediana do tempo até o melhor K; menor CPU média; por fim ID textual.
O pooling dos quatro métodos seleciona uma configuração comum, sem ajustar
parâmetros específicos a cada mecanismo. O critério só é aplicado à matriz
completa e revalidada. Não são usadas instâncias ou resultados finais.

Comandos, executados da raiz:

```bash
python3 scripts/calibrar.py --executar
python3 scripts/calibrar.py --analisar
```

O primeiro comando reutiliza a orquestração retomável. O segundo confere recibos,
hashes, CSVs e soluções, exige 160 execuções e produz resumo, tabela por método e
congelamento. Dados brutos e ambiente ficam em results/calibration/cal21_*.
O congelamento cria config/congelada_v1.cfg em modo somente leitura e um selo
JSON com SHA-256, protocolo e referências dos contratos; arquivos existentes
nunca são substituídos por uma escolha diferente. SHA-256 e recusa de sobrescrita
são a garantia lógica de imutabilidade; chmod não impede o proprietário de editar.
Mudanças futuras devem gerar nova versão, sem alterar o arquivo congelado.
