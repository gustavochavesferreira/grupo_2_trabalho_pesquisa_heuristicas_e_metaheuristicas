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

## Tarefa 11 — VNS, orçamento e Hbase

- **Perturbação:** sorteiam-se sem reposição `min(chapas_perturbadas, K)` chapas,
  juntam-se suas cópias, embaralha-se o conjunto e redistribui-se circularmente
  entre as selecionadas, com deslocamento inicial uniforme. Reempacotam-se somente
  essas chapas, em ordem crescente de índice. A distribuição pode repetir uma
  composição anterior; não se força uma mudança por tentativas ilimitadas. Esse
  procedimento mantém K e todas as cópias, sem acrescentar um critério de aceitação
  à perturbação. A aceitação ocorre depois do VND, como no Algoritmo 1.
- **Configuração provisória:** duas chapas perturbadas, até cinco perturbações/reinícios
  e 1000 avaliações de candidatos por tentativa de redução. São valores
  explícitos em `ConfigHbase`, ainda não calibrados nem congelados. `max_reinicios`
  limita as chamadas de perturbação; os reinícios internos do VND não o consomem.
  O orçamento de avaliações é compartilhado por todas as descidas da redução e
  reiniciado após uma redução aceita. Valor zero desliga a tentativa de reparo.
  Antes de iniciar uma vizinhança, reserva-se capacidade para toda a amostra;
  se ela não couber, interrompe-se o reparo sem aceitar amostra parcial.
- **Integração:** constrói-se uma solução validada, calcula-se LBref e tenta-se
  reduzir K. Executa-se VND(X); se continuar inviável e houver orçamento, executa-se
  VND(Perturba(X)). O estado perturbado só substitui X por melhoria estrita.
  Soluções globais só mudam após conversão e validação independente, com menos
  chapas. Após aceitar uma redução, começa nova tentativa; a primeira redução
  não reparada encerra Hbase. A semente inicializa um único `mt19937` por execução.
- **CPU:** `clock_gettime(CLOCK_PROCESS_CPUTIME_ID)` mede o processo desde antes
  da construção, incluindo limites inferiores, validações e busca. O mesmo relógio
  opcional atravessa VND, perturbação, empacotamento, decodificação e geração de
  cantos; chamadas antigas sem relógio preservam seu comportamento. Se o prazo
  expirar durante um candidato ou uma amostra, eles não são aceitos parcialmente;
  devolve-se a última solução factível. Se ainda não houver solução inicial
  completa, lança-se `TempoEsgotado`, sem fabricar resultado. As checagens são
  cooperativas: uma operação atômica, como validação ou ordenação, pode terminar
  após o prazo; o tempo efetivo é informado sem truncamento. A parada por CPU não
  garante o mesmo número de operações entre máquinas.
- **Verificação:** redução conhecida de três para duas chapas, alcance inicial de
  LBref, falha de reparo sem perda da incumbente, limites de reinícios e avaliações,
  rejeição de configurações inválidas, interrupção antes da construção e durante
  a busca, perturbação reproduzível e casos bidimensionais. A reprodução exata é
  conferida com limite de CPU folgado e parada por critérios de operações/LBref.
  Não foram executados calibração, piloto ou benchmark.

## Tarefa 12 — Hext

- O histórico usa um vetor de multiplicidades por índice de tipo como chave da
  composição, independente da ordem/IDs das cópias. O e F contam cópias por
  tentativa (inclusive demandas repetidas), somente nas oito falhas sem excesso.
  A marca `contabilizado` acompanha o resultado e suas cópias. A atualização ocorre
  na geração do empacotamento, antes de ele ser armazenado ou copiado; consultas
  de pesos não atualizam nada. Resultados de candidatos rejeitados também alimentam
  o histórico: são oportunidades observadas na mesma tentativa de redução.
- O contexto compartilhado transporta histórico e métricas por VND, remoção e
  perturbação. A arquitetura de Hbase é reutilizada por Hext; somente a seleção
  de bases muda. A cada nova redução limpa-se o mapa, preservando os contadores
  acumulados da execução. Não se recontam resultados anteriores após esse reinício.
- A amostragem ponderada usa `discrete_distribution`, removendo cópia e peso após
  cada sorteio. Peso é 1+F/max(1,O), sem excluir tipos. Conta-se movimento orientado
  quando a base tinha peso maior que 1 no instante da amostragem; a melhoria aceita
  usa esse mesmo indicador, congelado antes de avaliar os candidatos.
- Testes: O=16/F=8 para duas cópias do mesmo tipo em oito falhas, contagem única
  após cópia/consulta, composição independente da ordem, pesos, amostra sem
  reposição e reproduzível, reinício, exclusão de chamadas completas/excessivas
  e integração com a arquitetura. Hbase mantém seus testes e seleção uniforme.

## Tarefa 13 — Hint

- A busca adicional inicia na melhor tentativa básica incompleta e antecipa a
  primeira rejeitada por inserção; esgotadas as até oito posições anteriores,
  tenta trocas nas mesmas posições, sempre da mais próxima à mais distante.
  Aceita a primeira melhoria lexicográfica (área, quantidade rejeitada), reinicia
  pela nova primeira rejeição e encerra em sucesso, ausência de melhoria ou 16
  decodificações adicionais no total da ativação, sem renovar o teto após melhorar.
- As métricas contam ativações, decodificações concluídas, melhorias aceitas e
  ativações que terminam completas. Chamadas já completas/excessivas não ativam
  o mecanismo. O contexto integra o mesmo empacotador aos fluxos de remoção,
  movimentos e perturbação, preservando as oito tentativas básicas separadas do
  resultado final. Hint mantém seleção externa uniforme e não coleta histórico.
- Uma trilha opcional de movimentos (origem, destino, operação), desativada na
  execução normal, permite verificar a ordem efetiva sem guardar cópias de todas
  as sequências. Os testes cobrem ordem de inserções/trocas, reinício após melhoria,
  teto de 16, conservação e integração. Um caso de oito tentativas falhas melhora
  área rejeitada de 5 para 4; dez quadrados 3x3 em chapa 10x10 exercitam exatamente
  16 avaliações sem melhoria, com área total que cabe na chapa.

## Tarefa 14 — Controle auxiliar Haleat

- Haleat reutiliza a mesma função interna de Hint: mesmos operadores, comparação,
  oito posições no máximo por rodada, teto global de 16 decodificações e mesmas
  condições de aceitação/parada. A diferença é sortear a peça e a ordem das posições.
  Sorteia-se uma posição entre 1 e n-1, pois a posição zero não tem predecessoras;
  as até oito posições são amostradas sem reposição entre todas as anteriores,
  mantendo o operador de antecipação. Inserção e troca usam a mesma lista sorteada.
  Após melhorar, sorteiam-se novamente peça e posições. O esforço efetivamente
  usado pode variar, como em Hint; o orçamento máximo é idêntico.
- O gerador é o mesmo da execução, passado explicitamente, sem sementes locais.
  O resultado identifica método Haleat e `controle_auxiliar=true`; a seleção externa
  continua uniforme e não há coleta de histórico. Não é uma quinta proposta.
- Testes cobrem 30 sementes, reprodução dos movimentos e do estado do gerador,
  orçamento, conservação, distinção das escolhas guiadas e integração validada.

## Tarefa 15 — Hcomb

- Hcomb ativa os dois mecanismos na arquitetura comum, sem duplicar VND, VNS
  ou empacotamento. Cada chamada termina as oito tentativas básicas, contabiliza
  suas falhas no histórico externo e só então chama a busca interna guiada.
  A busca recebe a melhor tentativa por cópia e preserva os resultados básicos;
  suas decodificações adicionais alteram apenas o resultado usado no reparo e as
  métricas internas. Uma nova chamada básica é uma nova observação; consultas
  repetidas ao mesmo resultado continuam protegidas pela marca `contabilizado`.
- Um registro opcional de eventos, desativado normalmente, protege a ordem de
  integração nos testes. No caso dirigido de chapa 8x7, oito falhas básicas
  alimentam O/F uma vez e a busca interna completa o empacotamento após onze
  decodificações adicionais. Os contadores externos são comparados aos obtidos
  diretamente das oito tentativas, incluindo após cópias e novas consultas.
- Os testes também conferem o caso de excesso de área sem histórico nem busca
  interna, a diferença entre Hext e Hcomb no mesmo empacotamento básico e duas
  execuções reproduzíveis da configuração combinada. Toda solução final passa
  pelo verificador independente. Não foram executados experimentos formais;
  os parâmetros seguem provisórios e a interface de execução pertence à Tarefa 18.

## Tarefa 16 — IBL e f7

- A Figura 2 e as equações (7)/(9) do artigo local de Zhao et al. foram conferidas
  no texto e na página renderizada. O IBL usa a base da peça em y=H e a direita
  em x=W, alternando deslocamentos máximos para baixo e para a esquerda, nessa
  ordem, até estabilizar. Os deslocamentos saltam até bordas de obstáculos; não
  enumeram pontos de canto nem permitem atravessar obstáculos até uma posição
  globalmente melhor. Só se tenta a chapa corrente; uma falha abre outra chapa
  com a peça em (0,0). Chapas anteriores não são revisitadas.
- A permutação guarda IDs originais dos tipos, com repetições e sinais. As
  ocorrências recebem as cópias daquele tipo na ordem da instância, para manter
  IDs únicos e reprodução. A correção de orientação afeta somente as dimensões
  e o indicador do posicionamento; não modifica o sinal do genótipo, como na
  Figura 2. Comprimento, tipos e multiplicidades inválidos são rejeitados.
- O perfil é integrado entre bordas verticais distintas, usando o maior topo em
  cada intervalo. Isso equivale à soma por colunas inteiras da equação (7), sem
  memória/tempo proporcionais a W e sem confundir perfil com área ocupada. f7
  usa o perfil apenas da última chapa. Como ele está em [1,WH], reduzir K tem
  prioridade estrita, inclusive comparando perfil cheio com perfil mínimo.
- Coordenadas e perfil seguem int64. Apenas f7 usa `__uint128_t`, disponível no
  GCC exigido: WH*(K-1) pode exceder inclusive uint64 em instâncias válidas com
  peças finas. Descartou-se ponto flutuante, que poderia alterar aceitação por
  empate. Não se calcula H+altura ao iniciar acima da chapa, evitando estouro.
- Testes cobrem demandas e IDs fora de ordem, correções de orientação, contatos,
  descida após deslocamento lateral, cavidades inacessíveis, abertura sequencial,
  perfil/f7 manuais, prioridade de K e extremos numéricos. Outros 250 casos com
  semente 1001 comparam a solução a uma simulação literal por unidades, o perfil
  a uma soma coluna a coluna e a factibilidade ao verificador independente.
  `make -j2 test` passou antes de iniciar a Tarefa 17.

## Tarefa 17 — RLS-f7

- A RLS é independente da arquitetura de reparo. A inicialização embaralha as
  ocorrências dos tipos e sorteia sinais independentes com probabilidade 1/2,
  usando um único mt19937 com semente explícita. Em cada iteração sorteia-se uma
  posição; com probabilidade 1/2 tenta-se uma troca, sorteando no máximo 10T
  posições até encontrar valor assinado diferente. Isso permite trocar +i com
  -i e proíbe trocar duas ocorrências iguais com o mesmo sinal. Sem parceiro,
  ou sem tentar troca, inverte-se o sinal da primeira posição.
- Todo candidato é decodificado e validado pelo IBL. Aceita-se f7 menor ou igual,
  inclusive empates e orientações cujo efeito foi corrigido pelo decodificador.
  Não se normalizam sinais depois de decodificar: isso alteraria o espaço e os
  movimentos do artigo. Como f7 prioriza estritamente K, a solução corrente
  também preserva o melhor K e o melhor f7 já aceitos.
- O teto padrão publicado é 100000000 avaliações, contando a inicial; valores
  menores são permitidos explicitamente para testes, sem ultrapassar esse teto.
  Conta-se uma avaliação quando a decodificação validada e f7 ficam completos.
  Trocas/inversões contam movimentos iniciados, podendo incluir um candidato
  interrompido por CPU. Aceitos e melhorias contam somente candidatos completos
  aceitos; melhorias são reduções estritas de f7. Há parada por LBref, teto ou CPU.
- O relógio do processo inicia antes da inicialização e inclui limites inferiores,
  busca, validações e registros. Um candidato que atravessa o prazo não substitui
  a incumbente. Antes da primeira solução completa, expirar lança TempoEsgotado,
  como em Hbase; depois dela, devolve-se a última solução aceita. Checagens são
  cooperativas, com o mesmo cuidado sobre operações atômicas da Tarefa 11.
- `tempo_melhor` é o primeiro instante do menor K, a medida principal do TP3;
  melhorar só o perfil ou aceitar empate não o reinicia. Os marcos 0.1, 1, 5,
  10, 30 e 60 segundos usam eventos de disponibilidade da inicial e reduções
  de K, nunca eventos futuros. Se a inicial ainda não existia, o marco fica
  explicitamente indisponível, sem K/desvio fictícios. Após parada antecipada,
  conserva-se a última incumbente nos marcos seguintes. O resultado é guardado
  em memória; CSV e interface permanecem na Tarefa 18.
- Testes conferem multiplicidades/sinais, ambos os operadores, +i/-i, fallback
  completo de 10T e T=1, comparação exata de f7 acima de 64 bits, orçamento
  inicial/unitário, aceitação de empates, redução de K, rejeição de piora e
  reprodução em 30 sementes. Há testes de CPU real, validação independente,
  configurações inválidas e marcos sintéticos com instantes conhecidos.
  Não foram executados calibração, piloto ou benchmark.

## Tarefa 18 — Interface e registro

- A CLI exige instância, método, configuração chave=valor, semente, CPU positiva e
  diretório de saída; exportar a solução é uma opção. Rejeita opções/chaves extras,
  duplicadas, ausentes ou numericamente inválidas, sem escolher sementes implícitas.
  A configuração fornecida contém os valores provisórios existentes. Estado/ID e
  todos os parâmetros carregados são registrados; não se declara congelamento
  científico antes da Tarefa 21. Menores tetos da RLS servem para testes.
- Um módulo de evolução agora é compartilhado pelas seis configurações. A função
  anterior da RLS permanece como delegação compatível. A arquitetura registra
  disponibilidade da construção e cada redução aceita, com as mesmas regras
  temporais da Tarefa 17. Não se alteraram movimentos, aceitação ou parâmetros;
  somente acrescentaram-se registros. O motivo de CPU também considera as
  operações finais cronometradas, como já ocorria na RLS.
- CSV versão 1, com uma linha por execução, precisão de double, f7 decimal exato
  de 128 bits e escape de caminhos/nome. Métricas inaplicáveis e marcos anteriores
  à inicial ficam vazios, distinguindo-os de zero. Unidades de avaliações diferem
  explicitamente entre candidatos externos e f7. Família segue os nomes do
  catálogo; arquivos fora do padrão ficam OUTRA. Nenhum manifesto é alterado.
- A camada de saída valida novamente a solução antes de criar arquivos e confere
  limites, tempos, evolução, parada e f7/perfil. A exportação reutiliza o formato
  da Tarefa 4. Nomes determinísticos incluem instância/método/semente/config_id;
  recusa-se sobrescrita, em vez de apagar ou substituir resultados. Retomada,
  coordenação de processos e publicação por arquivo temporário ficam na Tarefa 20.
- Preservou-se a fronteira de CPU das Tarefas 11/17: leitura/configuração e saída
  em disco ficam fora do método; construção, limites, busca, validações internas
  e evolução estão dentro. As checagens cooperativas e a ausência de resultado
  antes da inicial continuam explícitas. A interface usa código 3 nesse caso,
  código 1 para outros erros e 0 no sucesso.
- Testes C++ e da CLI real cobrem argumentos/configurações inválidos, evolução
  com tempos conhecidos, rejeição de resultados inválidos antes de criar saída,
  proteção contra sobrescrita, CSV/solução, escape e f7 acima de uint64. Não
  houve calibração, piloto ou benchmark. Detalhes em docs/execucao.md.

## Tarefa 19 — Integração das seis configurações

- Um alvo separado `make integration-test` mantém a integração explícita, sem
  iniciar experimentos. A Tarefa 18 passou em `make -j2 test` antes deste trabalho.
  Usam-se seis casos pequenos, quatro em tests/data/integracao/ e dois já
  existentes, cobrindo LBref inicial, redução conhecida, falha de reparo/teto da
  RLS, orientação interna, demandas repetidas, rotação e áreas acima de 32 bits.
- A matriz C++ faz 144 execuções (seis métodos, seis instâncias, duas sementes,
  duas repetições). Confere solução pelo verificador independente, cópias/tipos,
  reprodução de posicionamentos e contadores, isolamento dos mecanismos,
  evolução, orçamentos e paradas. Mais seis execuções verificam interrupção por
  CPU real sem perder a incumbente. Comparações reproduzíveis usam teto de
  operações e CPU folgada; contagens sob interrupção temporal não são comparadas.
- Pela CLI, 48 execuções repetidas cobrem quatro casos e todos os métodos. Um
  leitor CSV e verificador geométrico em Python, independente dos módulos C++,
  reconstrói as soluções exportadas e confere demandas, cópias, orientações,
  contenção e ausência de sobreposição. Perfil/f7 são conferidos por soma de
  colunas. O cabeçalho, aplicabilidade das métricas, configuração, LBref,
  evolução e controle auxiliar também são verificados. Outras 12 chamadas
  exercitam CPU com e sem inicial, conferindo presença/ausência de arquivos.
- As execuções de cada teste são sequenciais, com sementes explícitas e saídas
  temporárias. Não se exigem tempos de CPU iguais entre repetições; exige-se
  igualdade de soluções e métricas de operações quando o limite temporal não
  encerra a busca. Não houve calibração, piloto, preflight ou benchmark.

## Tarefa 20 — Orquestração retomável

- O orquestrador Python usa a CLI existente, sem modificar algoritmos. Os modos
  calibration/pilot usam somente o piloto; preflight/final somente o conjunto
  final disjunto. Pilot/final exigem dez sementes comuns e 60 segundos; preflight
  usa uma semente e CPU curta. Calibration permite subconjuntos e orçamentos
  reduzidos, sem definir ainda a grade da Tarefa 21. As sementes 1001–1010 são
  versionadas e conferidas exatamente. O planejamento não executa métodos.
- Um contrato por modo/configuração preserva plano, parâmetros, hashes de dados,
  manifestos, sementes, configuração, fontes/executável/scripts e ambiente. Uma
  mudança exige outro lote, em vez de misturar resultados. Uma assinatura de
  código/compilador/flags força rebuild quando necessário, evitando atribuir
  opções novas a objetos antigos. Não se executam comandos Git.
- Sempre se conserva a solução completa: a retomada não confia apenas no campo
  validada. Um validador de arquivos confere identidade, parâmetros, métricas,
  evolução e geometria, além de perfil/f7, complementando o verificador C++.
  CSV/solução e recibo com hashes são obrigatórios para pular uma execução.
- Publica-se um diretório completo por renomeação atômica no mesmo filesystem,
  após validação dos CSVs temporários e retorno zero. Versões inválidas são
  preservadas em invalidos/ e refeitas; outras execuções não são apagadas.
  Tentativas interrompidas/falhas ficam em .pendentes/, sem aparência de conclusão.
- Uma trava global flock serializa orquestradores, inclusive com saídas distintas.
  O filho cronometrado herda a trava, protegendo contra morte abrupta do pai;
  Ctrl+C encerra e aguarda o filho. A garantia abrange processos iniciados pelo
  orquestrador; execuções oficiais devem passar por ele. Não se altera a fronteira
  de CPU das tarefas anteriores. Compilação e auditoria externa não são busca.
- Testes usam apenas saídas temporárias, instância real A42 com reparo desligado,
  corrupção de CSV/geometria, retomada, preservação, mudança de protocolo, trava,
  herança, interrupção e falha antes da inicial. Os planos completos são testados
  sem executá-los. Não houve calibração, piloto, preflight ou benchmark formal.
  O protocolo e os comandos estão em docs/experimentos.md.

## Revisão antes dos experimentos

- Conferidos o fluxo do TP3, a implementação, os documentos de execução e o
  estilo do código de exemplo. Mantiveram-se estruturas/funções diretas, nomes
  em português, using namespace std e referências para estruturas grandes ou
  modificadas. Move é usado somente para transferir resultados que não voltam a
  ser consultados, evitando copiar estados com oito empacotamentos por chapa.
- O inferior-esquerdo agora percorre as coordenadas projetadas de forma preguiçosa
  e encerra no primeiro canto/orientação admissível, na mesma ordem (y,x,rotação).
  Não materializa/filtra a grade inteira antes de inserir. A API pontos_canto
  permanece disponível; os oráculos e testes de desempate protegem a equivalência.
- No IBL, o relógio é consultado a cada bloco de até 64 obstáculos, além das
  verificações externas. O perfil usa a mesma frequência no laço interno. Isso
  reduz o custo de clock_gettime sem alterar coordenadas, orientações, f7 ou RNG.
  A resposta ao prazo continua cooperativa. A composição para consultar os pesos
  é calculada uma vez por amostra, sem mudanças nas contagens do histórico.
- Corrigida a aceitação de uma redução em Hbase após a validação atravessar o
  prazo: verifica-se CPU antes de substituir a incumbente. Teste dirigido com
  relógio expirado confere preservação da solução, métricas e eventos.
- A retomada agora exige o cabeçalho completo da versão 1, inclusive campos
  inaplicáveis, e o cabeçalho exato da solução. Um marco posterior ao término
  precisa conservar K final. Foram adicionadas regressões para esses casos.
  Carimbo auxiliar de compilação inválido provoca rebuild, não interrompe a
  preparação. Retirou-se a auditoria geométrica duplicada antes de publicar uma
  execução nova; a retomada continua revalidando cada execução existente.
- A revisão de desempenho usou orçamento de operações igual, semente 1001 e
  saídas temporárias: os posicionamentos, K e avaliações foram idênticos antes e
  depois nos seis casos medidos. Não há resultados formais a refazer. Detalhes,
  alcance da revisão e prontidão estão em docs/revisao_pre_experimentos.md.

## Tarefa 21 — Calibração e congelamento

- Plano registrado antes da coleta em docs/calibracao.md: quatro opções de um
  fator por vez em torno de (2 chapas, 5 reinícios, 1000 candidatos), examinando
  respectivamente 3 chapas, 10 reinícios e 2000 candidatos. Mesma grade para
  Hbase/Hext/Hint/Hcomb; somente dez instâncias-piloto, semente 1001, três segundos.
  Uma grade cartesiana grande foi descartada para reduzir custo e sobreajuste;
  uma semente e ausência de interações são limitações explícitas, não evidência
  sobre desempenho formal. São 160 execuções válidas, sem uso do conjunto final.
- Critério prévio comum: menor desvio médio, maior alcance de LBref, menor mediana
  até melhor K, menor CPU média, ID. Seleciona parâmetros agregando igualmente
  os quatro métodos; não seleciona H*. Todas as opções empataram em qualidade,
  e base venceu no desempate temporal, com diferenças pequenas e sem inferência
  estatística. Foram congelados 2/5/1000 para todas as propostas.
- Configuração congelada v1 e selo SHA-256 nunca são substituídos por conteúdo
  diferente; configuração/selo são somente leitura. O verificador confere os
  hashes de configuração, sementes e plano. A reanálise exige matriz completa,
  recibos, mesma configuração/ambiente e revalida as soluções. A retomada pulou
  as 160 execuções já válidas. Resultados brutos e resumos foram preservados.
- A coleta local ocorreu em Ryzen 3 5300U, diferente do Ryzen 5 5600 previsto no
  TP3. O ambiente real está registrado, sem alegar execução no hardware previsto.
  Essa diferença deve ser resolvida antes do piloto formal (máquina prevista ou
  alteração expressamente autorizada do protocolo). Não se iniciou a Tarefa 22.

## Tarefa 23 — Pré-execução antes do piloto formal

- Por autorização do usuário, a ordem passou a 21 → 23 → 22, mantendo o piloto
  formal pendente. O Ryzen 3 foi autorizado para as etapas locais, com ambiente
  real registrado e sem compensação artificial de CPU entre máquinas.
- Foram fixados três segundos de CPU e semente 1001 para cada um dos seis métodos
  nas 153 instâncias finais: 918 execuções, sem interseção com o piloto. O limite
  curto permite a construção dos casos grandes; não substitui o orçamento formal.
  A configuração congelada da Tarefa 21 foi preservada e seu selo foi conferido.
- A passagem terminou com 918 resultados válidos. Uma auditoria completa conferiu
  matriz, contratos, hashes, CSVs e soluções antes e depois da retomada. Na segunda
  execução do comando, as 918 foram puladas; nenhum recibo foi alterado. Não houve
  falha que exigisse modificar algoritmos, parâmetros ou repetir a calibração.
- O auditor produz somente contagens e comprovação técnica, sem rankings, seleção
  de H* ou ajuste a partir do conjunto final. Dados brutos permanecem localmente
  em results/preflight/congelada_v1/, fora dos resultados científicos e do Git;
  plano, integridade e prova da retomada são versionáveis. Detalhes e comandos
  constam em docs/preflight.md. Não se iniciou a Tarefa 22.
