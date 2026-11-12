# Piloto formal — execução pelo usuário

Na raiz do repositório, execute somente:

```bash
python3 scripts/piloto.py
```

O comando compila quando necessário, confere o selo de congelamento e usa o
orquestrador sequencial para dez instâncias-piloto, Hbase/Hext/Hint/Hcomb, dez
sementes comuns e 60 segundos de CPU: 400 execuções válidas. O usuário autorizou
Ryzen 3 para este piloto; ambiente real e parâmetros são registrados. Nenhuma
instância final participa. Não são necessárias opções para escolher parâmetros.

Uma barra mostra execuções concluídas/total e porcentagem, incluindo as
validadas na retomada. Ela avança entre execuções, sem estimar progresso interno
de uma execução. A apresentação fica no comando do piloto, preservando o
orquestrador e seus hashes/contratos existentes.

Mantenha o terminal aberto e o computador sem suspender. O teto teórico é de
6h40 de CPU, além das operações de preparação e auditoria; execuções que atingem
LBref ou encerram o reparo podem terminar antes. Não rode outros lotes/CLIs dos
algoritmos em paralelo. Ctrl+C interrompe com preservação dos resultados completos.
Repita o mesmo comando para retomar: resultados válidos são conferidos e pulados;
parciais/inválidos são refeitos segundo o protocolo de orquestração.

Ao concluir, o mesmo comando audita toda a matriz antes de analisar. Seleciona
H* por menor desvio médio, depois maior alcance de LBref e depois menor tempo
mediano até o melhor K. O desvio médio usado na decisão é racional exato,
recalculado a partir de K/LBref, evitando desempatar por erro de arredondamento.
Se persistir igualdade exata nos três critérios, preserva a ordem Hbase, Hext,
Hint, Hcomb e informa todas as empatadas no selo, sem alegar vencedor exclusivo.

Saídas automáticas:

- results/pilot/congelada_v1/execucoes/: 400 CSVs, soluções, recibos e logs.
- results/pilot/congelada_v1/: contrato, ambiente, configuração e pendências.
- results/pilot/resumo.csv: quatro linhas de resumo, uma por método.
- results/pilot/integridade.json: comprovação de matriz completa e validada.
- config/h_estrela_v1.json: identidade de H*, critérios, resumo, ambiente e hashes
  da configuração, sementes, manifesto piloto e contrato.

O selo de H* é somente leitura e recusa qualquer conteúdo diferente. Repetir o
comando audita os mesmos dados e preserva a escolha. Uma matriz incompleta não
congela H*. Erros retornam código não zero; a mensagem de sucesso é
"Piloto concluído: 400 execuções validadas. H* = ...".

Para conferir somente o planejamento, sem executar métodos, há --planejar.
Para auditar/analisar somente dados já existentes, há --analisar. Essas opções
são auxiliares; não são necessárias para a execução normal acima.

O desenvolvimento desta tarefa não executou o piloto pelo usuário. Foram feitos
somente testes da lógica de seleção, do requisito de 100 execuções por método,
da recusa de análise incompleta e do planejamento de 400 execuções.
