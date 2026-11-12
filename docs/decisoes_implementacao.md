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

## Tarefa 3 — Catálogo e seleção

- **Validação compartilhada:** o script Python usa um pequeno executável de
  metadados ligado ao leitor C++ da Tarefa 2. Evita-se um segundo parser do formato
  unificado e divergências entre catálogo e algoritmos. Todos os arquivos
  reconhecidos são validados, inclusive CLASS fora da seleção. Testes usam dados
  reais e cópias temporárias com remoção, duplicação, nome inválido e corrupção.
- **Identificação e reprodução:** nomes originais definem a família e os campos
  de CLASS; caminhos são relativos a `instances/source/`. O identificador é o
  nome sem extensão, comparado textualmente no desempate das A. CSVs incluem
  SHA-256 do original e seguem a ordem dos caminhos para reprodução estável.
  Não se renomeiam arquivos nem se deduz a classe pelas dimensões. Os testes
  conferem hashes, seleção exata, repetibilidade dos CSVs, contagens e disjunção.
- **Completude:** exige-se toda a entrada necessária ao piloto/final; CLASS
  adicionais válidas são catalogadas, sem exigir réplicas não usadas pelo TP3.
  Descartou-se restringir o catálogo às 163 selecionadas, pois isso ocultaria
  dados fornecidos. Arquivos auxiliares README e descrição de formato são
  ignorados explicitamente; outros nomes não reconhecidos causam erro.
