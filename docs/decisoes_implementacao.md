# Decisões de implementação

Este registro é cumulativo e preserva as decisões não determinadas diretamente pelo
TP3, pelas fontes acadêmicas ou pelo código existente. Cada entrada futura deve
informar a tarefa, a decisão, a justificativa, as alternativas relevantes descartadas
e os testes que a protegem. Revisões devem explicar seu impacto nas tarefas e nos
resultados anteriores.

## Estado inicial — Tarefa 1

Ainda não há decisões de implementação registradas.

## Tarefa 2 — Leitura e identificação das cópias

- **Representação e ordem:** tipos permanecem na ordem do arquivo; cópias recebem
  IDs de 1 até o total demandado nessa ordem e guardam o índice do tipo no vetor.
  O ID original fica no tipo. Isso mantém vínculos válidos ao copiar uma instância,
  sem ponteiros nem ordenação implícita. Descartou-se usar o ID original como índice
  direto: a ordem das linhas pode variar. O teste válido usa IDs fora de ordem e
  confere demandas, vínculos, unicidade e repetição da leitura.
- **Contrato do leitor:** IDs únicos de 1 a m, conforme o formato da 2DPackLib;
  uma linha não vazia para m, outra para W H e m linhas com seis campos. Linhas
  em branco, espaços e CRLF são aceitos; campos ou registros excedentes são
  rejeitados. Não se adotou leitura livre por tokens, pois ela esconderia linhas
  incompletas. Os testes cobrem erros estruturais e numéricos com arquivo e linha
  no diagnóstico. Falhas lançam `std::runtime_error`, sem devolver instâncias parciais.
- **Campos e limites:** dimensões, demandas, IDs e áreas usam inteiros de 64 bits;
  produtos e somas são verificados antes da expansão. `bi` é preservado como inteiro
  e `pi` como número real finito, sem limitar a demanda nem mudar o objetivo.
  Rejeitam-se peças que não cabem nem rotacionadas em uma chapa vazia; a orientação
  original é preservada quando somente a rotação cabe. Evitaram-se limites
  arbitrários para o tamanho das instâncias. Os testes cobrem áreas acima de 32
  bits, estouros de produto e soma, campos auxiliares e as duas situações de encaixe.
