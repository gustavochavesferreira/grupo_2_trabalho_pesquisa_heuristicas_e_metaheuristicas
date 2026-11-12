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

## Tarefa 6 — Empacotador-base multissequência

- **Execução e retorno:** quando a área cabe, são executadas as oito tentativas
  solicitadas na Tarefa 6, mesmo se alguma já for completa, preservando todos os
  resultados para os mecanismos posteriores. O índice da melhor identifica o
  resultado sem duplicá-lo. O excesso de área retorna área total e excesso,
  vetor de tentativas vazio e índice -1, sem decodificar nem consumir o gerador.
  Não se atribuem rejeições geométricas fictícias a uma chamada descartada por área.
- **Escolhas aleatórias:** usa-se `mt19937` recebido por referência, sem fonte
  interna de sementes. Em cada tentativa aleatória, escolhe-se uniformemente
  entre as primeiras `min(ceil(sqrt(|S|)), restantes)` peças da lista ordenada;
  `|S|` é o tamanho inicial do conjunto da chamada. A lista remanescente mantém
  sua ordem após a remoção, sem reposição. A ordenação inicial é decrescente por
  área, maior lado, menor lado e ID da cópia.
- **Sequência anterior:** vetor vazio significa ausência de uma sequência útil,
  produzindo uma sétima tentativa aleatória além das seis usuais. Caso contrário,
  remove-se quem saiu do conjunto, preserva-se a ordem relativa de quem ficou e
  acrescentam-se as novas peças em ordem decrescente. Não se reordena toda a
  sequência anterior, pois isso perderia a informação reaproveitada. IDs
  desconhecidos e duplicados são erros; peças válidas que saíram são removidas.
- **Seleção:** minimiza área rejeitada e depois quantidade de rejeições. Empates
  finais preservam a tentativa de menor índice, inclusive entre completas.
  Testes cobrem descarte, oito tentativas, ordenação, atualização, escolhas na
  lista restrita, seleção, índices de chapa, entradas vazias/inválidas e
  reprodução. Casos aleatórios usam sementes fixas e as tentativas são conferidas
  pelo verificador independente após completar as rejeições em chapas individuais.

## Tarefa 7 — Construção inicial

- **Inserção incremental:** a busca da posição inferior-esquerda foi extraída do
  decodificador para `insere_inferior_esquerdo`, usada também pela construção.
  Ela insere somente a nova peça e preserva a chapa se falhar. Isso evita duplicar
  a regra geométrica ou reempacotar peças já posicionadas, o que poderia alterar
  a construção prevista. Os testes anteriores do decodificador permanecem ativos.
- **Escolha da chapa:** após ordenar cópias por área, maior lado, menor lado e ID,
  todos decrescentes, examinam-se chapas por maior área ocupada e menor índice.
  Para uma peça fixa, isso equivale à menor folga de área após a inserção.
  Chapas sem área suficiente são descartadas; a primeira com posição geométrica
  viável recebe a peça. Empates de folga priorizam o índice menor, preservando a
  ordem de abertura. Não se abre chapa apenas porque uma candidata falhou.
- **Validação e testes:** toda solução inicial passa pelo verificador independente
  antes de retornar. Falhar em chapa vazia gera erro, sem devolver solução parcial.
  Testes cobrem demandas repetidas, ordenação, desempates, melhor aproveitamento,
  bloqueio apesar da área livre, preservação em falha e rotação em chapa vazia
  e ocupada. Outros 100 casos pequenos com semente 1001 são comparados com um
  oráculo que enumera posições inteiras sem a geometria compartilhada.

## Tarefa 8 — Limites inferiores

- **Fonte e definição:** implementado o limite DMV da equação (8), usando CUTSQ,
  Lema 2 e Teorema 3 do artigo original de 2002, consultado em texto e nas páginas
  renderizadas para conferir as desigualdades. `LBref` combina esse limite com
  a área original, conforme o TP3. O reforço opcional por L4 orientado não foi
  acrescentado: ele é um limite adicional, não a definição da equação (8).
- **Representação e cálculo:** quadrados de mesmo lado são agrupados, incluindo
  demandas. São avaliados zero e os lados distintos até H/2 (Corolário 4),
  recalculando os conjuntos para manter o código direto, em vez da atualização
  incremental do artigo. A forma equivalente da equação (7) usa somas de área e
  desperdício em `uint64_t`, evitando produtos de área por número de chapas e
  estouro intermediário. Não se usam arredondamentos em ponto flutuante nos limites.
- **Verificação:** exemplo publicado (área 4, DMV 6), decomposição da Figura 1,
  casos manuais, 300 comparações com fórmulas literais e todos os limiares e 60
  ótimos exatos pequenos, com semente 1001. Casos extremos cobrem numeradores acima
  de int64 e decomposição com muitos quadrados sem expansão em memória.
  Desvios com LBref não positivo ou K abaixo do limite são rejeitados para não
  aceitar métricas inconsistentes. Detalhes em `docs/limites_inferiores.md`.

## Tarefa 9 — Estado de reparo e eliminação de chapa

- **Representação:** cada chapa de reparo mantém sua composição completa, o
  resultado geométrico atual e as tentativas básicas. A composição é a fonte de
  todas as peças atribuídas, mesmo quando não há posicionamento. Na conversão
  de uma solução validada, preservam-se as posições sem simular tentativas.
  A inviabilidade é calculada sob demanda, evitando um total global desatualizado.
- **Excesso e rejeições:** chamadas descartadas por área não ganham rejeições
  geométricas fictícias. Contribuem com excesso e uma chapa inviável; só chamadas
  efetivamente decodificadas contribuem com área e quantidade rejeitadas. Ao
  reempacotar com excesso, descartam-se posições antigas e preserva-se apenas a
  sequência anterior para eventual reutilização. Essa sequência histórica pode
  diferir da composição atual; o empacotador-base a atualiza quando a área couber.
  Comparam-se estados estritamente por excesso, área rejeitada, chapas inviáveis
  e peças rejeitadas, nessa ordem, conforme o TP3.
- **Remoção e redistribuição:** remove-se a menor área ocupada, desempatando pelo
  menor índice. As peças removidas seguem área, maior lado, menor lado e ID,
  todos decrescentes. A receptora minimiza excesso após a atribuição; em empate,
  minimiza folga não negativa e índice. Isso dá preferência ao melhor encaixe por
  área e, quando nenhuma chapa comporta a peça por área, à menor sobrecarga.
  Não se usa aleatoriedade na atribuição nem custo geométrico adicional para
  escolher receptoras. Somente as receptoras são reempacotadas, uma vez após a
  redistribuição, em ordem de índice; as demais preservam a geometria reindexada.
- **Aceitação e testes:** a origem precisa ser uma solução validada com pelo
  menos duas chapas. A conversão do reparo para solução exige inviabilidade zero,
  igualdade entre atribuições e posicionamentos por chapa e validação independente.
  A origem nunca é alterada. Testes cobrem as quatro prioridades, empates,
  redistribuição, excesso, falha geométrica, conservação, rejeição de estados
  inválidos, áreas de 64 bits e reprodução com sementes fixas. Não há VND/VNS
  nesta tarefa.

## Tarefa 10 — VND e vizinhanças externas

- **Origem e amostra:** escolhe-se a maior sobrecarga; sem sobrecarga, a maior
  área rejeitada. Empates preservam o menor índice. Em cada visita a uma
  vizinhança, Fisher-Yates parcial sorteia uniformemente e sem reposição
  `min(ceil(sqrt(T)), peças da origem)` bases; T é o total de cópias da instância.
  Cada base produz um candidato, salvo se não houver parceiro ou receptora.
  Não se encerram avaliações ao encontrar a primeira melhoria, nem ao encontrar
  um candidato factível: toda a amostra é examinada sobre o mesmo estado original.
- **Receptora e parceiros:** para a área de entrada, usa-se o critério da Tarefa 9:
  menor excesso resultante, menor folga não negativa e menor índice. Na troca,
  a escolha é feita para a entrada da peça-base, entre chapas não vazias; depois,
  o parceiro minimiza a soma das sobrecargas das duas chapas após a troca,
  desempatando pela diferença absoluta de áreas e pelo menor ID. No par, a segunda
  peça é sorteada uniformemente entre as outras cópias da origem e a receptora
  é escolhida para a área conjunta. Não se enumeram todas as receptoras, parceiros
  ou pares: essas escolhas seguem as regras de construção de candidatos do TP3.
- **Movimentos e aceitação:** realocação move a base, troca move uma cópia em cada
  sentido e par move duas cópias distintas. Cada candidato reempacota somente
  origem e receptora, em ordem crescente de índice, com o gerador explícito.
  Empates finais preservam o primeiro candidato da amostra. Aceita-se apenas a
  melhor melhoria estrita e reinicia-se na primeira vizinhança. Sem melhoria,
  avança-se; o VND termina em estado factível ou após falhar nas três vizinhanças.
  Os contadores registram avaliações, melhorias por vizinhança e reinícios.
- **Chapas vazias no reparo:** movimentos podem esvaziar chapas. Elas permanecem
  como posições do estado durante a descida, mantendo índices estáveis. A conversão
  para solução agora omite chapas realmente vazias e reindexa as restantes, após
  conferir os índices originais e as atribuições. O verificador de soluções segue
  rejeitando chapas vazias. Essa extensão da conversão da Tarefa 9 não modifica
  soluções anteriores e não requer refazer resultados.
- **Testes:** há melhorias conhecidas nas três vizinhanças, incluindo uma troca
  que permite nova melhoria por realocação e testa o reinício. Conferem-se limite
  e unicidade da amostra, avaliação de todos os candidatos, escolha da melhor,
  preservação de chapas inalteradas, compactação, conservação, erros de entrada
  e reprodução. Outros 60 estados com semente fixa passam pela descida; a
  geometria é conferida independentemente, completando rejeitadas em chapas
  individuais somente nos testes. Estados reparados passam pela conversão validada.
