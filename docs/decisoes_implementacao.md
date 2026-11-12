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

## Tarefa 4 — Solução e verificação independente

- **Representação:** chapas são identificadas por posição no vetor, a partir de
  zero. Cada posicionamento guarda também esse índice, conferido pelo verificador,
  além do ID da cópia, coordenadas, dimensões usadas e indicador de rotação.
  O tipo é consultado na instância, evitando uma segunda atribuição de tipo que
  possa divergir da origem. Rejeitam-se chapas vazias para que o tamanho do vetor
  corresponda ao número de chapas efetivamente usadas. Testes cobrem índices
  inconsistentes, cópias ausentes/duplicadas/desconhecidas e demandas por tipo.
- **Verificação:** retorna o primeiro erro, compara todos os pares dentro de cada
  chapa e usa desigualdades estritas para sobreposição. A contenção é verificada
  antes das somas de coordenadas, evitando estouro mesmo em entradas malformadas.
  Não se usa uma rotina de posicionamento como verificador. Os testes incluem
  rotação, quadrados, bordas, vértices, chapas distintas e coordenadas extremas.
- **Persistência:** CSV versão 1, documentado em `docs/formato_solucao.md`, uma
  linha por cópia e interpretação junto da instância. A solução é validada antes
  de abrir a saída; descartou-se gravar estados parciais ou inviáveis neste formato.
  Testes conferem o conteúdo, falha de abertura e preservação do arquivo existente
  quando a solução é inválida. A interface experimental continua reservada à Tarefa 18.

## Ajuste de estilo solicitado pelo usuário

Usar `using namespace std`, seguindo o código de exemplo, e passar valores simples
por valor, sem acrescentar `const` ou referências por padrão. Referências ficam
restritas a motivos concretos: evitar cópias de instâncias, soluções e vetores;
operar sobre streams; modificar elementos existentes; e capturar exceções sem
perder seu tipo dinâmico. Os parâmetros de entrada grandes permanecem `const`
para permitir consulta sem cópia nem alteração. Esse padrão vale para as próximas
tarefas. A revisão modifica somente o estilo; os testes existentes verificam a
preservação do comportamento.

## Tarefa 5 — Cantos e decodificação de uma chapa

- **Construção dos candidatos:** cruzam-se as coordenadas das bordas direitas e
  superiores das peças colocadas, incluindo zero, para obter cantos projetados
  também entre peças diferentes. Coordenadas repetidas, pontos ocupados e pontos
  nas bordas superior/direita da chapa são removidos. Para cada orientação,
  descartam-se candidatos inviáveis e os redundantes que ainda permitem mover
  uma unidade para baixo ou para a esquerda. Assim, não se depende apenas dos
  dois vértices imediatamente adjacentes à última peça nem se aplica dominância
  por coordenadas que possa eliminar um canto útil atrás de um obstáculo.
- **Desempates:** menor y, menor x e orientação original antes da rotacionada.
  Quadrados são examinados uma única vez. O decodificador sempre processa toda
  a sequência, sem abrir chapas nem reordenar peças. IDs desconhecidos ou
  repetidos são erros; subconjuntos sem repetição são permitidos para reempacotar
  chapas. O resultado preserva a sequência, colocadas em ordem, rejeitadas em
  ordem, área rejeitada, ID e posição da primeira rejeição (ambos -1 se ausente).
- **Verificação:** geometria em módulo próprio, sem reutilização pelo verificador
  independente. Testes dirigidos cobrem contato, rotação, quadrados, cantos,
  bloqueios, continuação após rejeição e áreas acima de 32 bits. Outros 200 casos
  com semente 1001 comparam o resultado com um oráculo que enumera todos os
  pontos inteiros. Ao completar cada resultado com chapas individuais para as
  rejeitadas, verifica-se também a conservação de todas as cópias pelo verificador.
