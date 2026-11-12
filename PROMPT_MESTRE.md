# Prompt mestre para implementação e experimentação das heurísticas do TP3

Você é um agente de IA responsável por implementar, testar e preparar os experimentos computacionais do trabalho descrito em `TP3 - Grupo 2 - Heurísticas e Metaheurísticas.pdf`.

Este prompt foi fornecido integralmente na mensagem atual do chat. Não presuma que exista uma cópia de `PROMPT_MESTRE.md` no projeto, não procure esse arquivo e não dependa dele durante a execução. As instruções desta mensagem são a fonte para identificar e executar a tarefa atual.

Execute somente a tarefa indicada no campo `TAREFA A EXECUTAR`, no final desta mensagem. Considere que todas as tarefas de número menor já foram concluídas e versionadas. Antes de alterar qualquer arquivo, leia os documentos, `docs/decisoes_implementacao.md` quando ele já existir e o código relacionados à tarefa atual, além de inspecionar o estado existente do projeto. Não refaça componentes já concluídos sem uma justificativa técnica clara.

## 1. Fontes obrigatórias e ordem de precedência

Use como fontes principais:

1. `TP3 - Grupo 2 - Heurísticas e Metaheurísticas.pdf`: especificação dos algoritmos, configurações, hipóteses e experimentos.
2. `Randomized_Local_Search_on_the_2D_Rectangular_Bin_Packing_Problem_with_Item_Rotation.pdf`: fonte da RLS-f7, de Zhao et al. (2024), DOI `10.1145/3638530.3654139`.
3. `enunciado/HeM - Roteiro dos trabalhos de pesquisa.pdf`: exigências do TP, TE e TA.
4. `codigo_exemplo/`: referência de simplicidade, organização, comentários, compilação e estilo. O problema e os algoritmos desse diretório são diferentes e não devem ser copiados como solução.
5. Artigos originais citados pelo TP3, quando forem necessários para implementar detalhes não contidos no projeto, especialmente o limite inferior de Dell'Amico, Martello e Vigo.

Se houver conflito, siga primeiro o TP3. Não altere silenciosamente um algoritmo, uma métrica ou um protocolo experimental. Quando faltar uma decisão que não possa ser deduzida das fontes ou do código já existente, aplique as regras de autonomia e interrupção definidas a seguir.

Quando o TP3 deixar intencionalmente uma escolha de implementação ou calibração em aberto e a tarefa atual exigir que ela seja definida, escolha a alternativa mais simples, justificável e reproduzível. Isso inclui, por exemplo, desempates ainda não definidos, representação interna, atualização de sequências, construção concreta de candidatos, forma da perturbação, distribuição de escolhas aleatórias e valores que serão posteriormente calibrados. A escolha deve preservar o objetivo do método, as diferenças planejadas entre as configurações e a igualdade das demais condições experimentais.

Registre decisões desse tipo em `docs/decisoes_implementacao.md`, explicando de forma breve: tarefa, decisão adotada, justificativa, alternativas relevantes descartadas e testes que a protegem. Esse arquivo pertence ao projeto e mantém o contexto entre mensagens, chats e agentes diferentes; ele não é uma cópia deste prompt. Antes de iniciar qualquer tarefa posterior à Tarefa 1, leia esse arquivo e preserve as decisões anteriores, salvo quando houver erro técnico demonstrável. Nesse caso, corrija a decisão, atualize o registro e informe claramente o impacto sobre tarefas e resultados anteriores. Não registre detalhes triviais que já sejam evidentes no código.

Interrompa e consulte o usuário somente quando a decisão puder alterar a variante do problema, a função objetivo, uma hipótese avaliada, a diferença isolada entre métodos, os conjuntos de instâncias, as sementes, os limites experimentais, os critérios estatísticos ou outro elemento científico fixado pelo TP3. Também interrompa quando duas interpretações plausíveis produzirem métodos materialmente diferentes e não houver base para preferir uma delas. Não interrompa por escolhas rotineiras de engenharia que possam ser tomadas e testadas segundo os critérios acima.

O artigo local confirma que a RLS-f7 trabalha com uma permutação com repetições e sinais, usa uma variante do Improved Bottom Left como decodificador, aplica troca ou inversão de sinal e avalia a solução por

`f7(s) = W * H * (K(s) - 1) + area_do_perfil_superior_da_ultima_chapa`.

## 2. Escopo global

O projeto deve chegar a uma versão reproduzível que:

- implemente em C++20 as quatro configurações propostas `Hbase`, `Hext`, `Hint` e `Hcomb`;
- implemente em C++20 a comparadora da literatura `RLS-f7`;
- implemente `Haleat` apenas como controle auxiliar de `Hint`, sem apresentá-la como uma sexta heurística proposta;
- leia as instâncias `A`, `BENG` e `CLASS` fornecidas pelo usuário no formato unificado da 2DPackLib;
- expanda demandas em cópias individuais identificadas, preservando o tipo de origem;
- valide todas as soluções antes de aceitá-las como resultado experimental;
- execute primeiro a calibração e o piloto e congele parâmetros e sementes antes do benchmark final;
- execute o benchmark final de 153 instâncias, 6 métodos, 10 sementes e 60 segundos de CPU por execução;
- gere arquivos de resultados, análises estatísticas, as duas tabelas e a figura previstas no TP3, prontos para serem usados no TA e no TE;
- permita retomar experimentos interrompidos sem perder resultados válidos nem duplicar execuções.

A redação do TE e a criação dos slides do TA estão fora deste prompt. O resultado final deve fornecer os dados, tabelas, figura e informações de reprodutibilidade necessários para produzi-los.

## 3. Regras permanentes de implementação

- Use C++20 e GCC para os algoritmos. Use uma única thread e um único processo cronometrado por vez nos experimentos oficiais.
- Mantenha a organização simples, preferencialmente com `include/`, `src/`, `tests/`, `scripts/`, `config/`, `instances/` e `results/`, além de um `Makefile` na raiz.
- O código deve parecer um bom trabalho de graduação: classes e estruturas diretas, funções com responsabilidade clara e nomes descritivos. Não crie camadas, padrões ou abstrações sem necessidade real.
- Não crie namespace próprio para o projeto. Use referências, `static`, templates ou recursos mais avançados apenas quando houver motivo concreto; não os acrescente como ritual de segurança ou sofisticação.
- Não quebre uma expressão em várias linhas somente por ela ser relativamente longa. Quebre linhas quando isso realmente melhorar a compreensão.
- Escreva comentários em português para explicar decisões ou trechos que não sejam óbvios. Evite comentários que apenas repitam o código e evite documentação formal excessiva.
- Use coordenadas inteiras. Use um tipo inteiro com capacidade suficiente para áreas, produtos e somas, evitando estouro nas maiores instâncias.
- Toda aleatoriedade deve partir de uma semente explícita e reproduzível. Um gerador deve ser passado ou armazenado de maneira clara; não misture fontes aleatórias não controladas.
- O limite oficial é de tempo de CPU, incluindo construção, busca, validações internas e demais operações do método. No Linux, prefira uma medição de CPU do processo, como `clock_gettime(CLOCK_PROCESS_CPUTIME_ID)`, encapsulada em uma função simples.
- Uma solução global só pode ser substituída por outra factível e validada. Estados inviáveis podem existir apenas durante o reparo das quatro configurações propostas.
- Não copie código externo sem necessidade. Se consultar a implementação publicada da RLS ou outra fonte, registre no README o que foi consultado e implemente a solução de forma compatível com a arquitetura deste projeto.
- Não deixe `TODO`, métodos vazios, dados fictícios ou testes que sempre passam.
- Não modifique os PDFs, o diretório `codigo_exemplo/` nem os materiais de consulta.
- As instâncias serão fornecidas pelo usuário em `instances/source/`. Não as baixe, não invente arquivos ausentes e não substitua silenciosamente um conjunto por outro. Mantenha esses arquivos brutos fora do Git por padrão; versione o manifesto, as instruções de preparação e os metadados necessários para reproduzir a seleção.

## 4. Testes e verificação

Use testes C++ simples em `tests/`, sem framework externo obrigatório. Um pequeno executável de testes, funções auxiliares de verificação e `assert` ou verificações equivalentes são suficientes. O `Makefile` deve oferecer, no mínimo, alvos claros para compilar o programa, compilar e executar os testes e limpar artefatos.

Cada tarefa deve executar os testes pertinentes e compilar com avisos habilitados. Depois que todas as heurísticas existirem, qualquer execução de teste ou benchmark deve passar a solução final pelo verificador independente. Testes aleatórios devem usar sementes fixas.

Testes importantes devem cobrir, conforme os componentes forem implementados:

- leitura correta, expansão das demandas e rejeição de instâncias inválidas;
- rotação, contenção, contato de bordas, sobreposição e atendimento exato das demandas;
- desempates determinísticos das rotinas construtivas;
- decodificadores inferior-esquerdo e IBL;
- cálculo do perfil superior e de `f7`;
- oito tentativas do empacotador-base, rejeições e seus desempates;
- comparação lexicográfica de estados inviáveis;
- movimentos das vizinhanças sem perda ou duplicação de peças;
- atualização única do histórico de `Hext`;
- limite de 16 decodificações adicionais de `Hint`;
- reprodutibilidade para a mesma instância, método, configuração e semente;
- retomada segura dos experimentos.

## 5. Regras sobre Git e entrega de cada tarefa

O usuário fará todas as operações de Git e GitHub. Você não deve executar `git init`, `git add`, `git commit`, `git push`, criar repositórios remotos, trocar branches ou alterar o histórico. Comandos Git somente de leitura também devem ser evitados; inspecione os arquivos diretamente.

Ao concluir a tarefa:

1. resuma o que foi implementado;
2. liste os arquivos criados ou alterados;
3. informe exatamente quais compilações e testes foram executados e seus resultados;
4. informe qualquer limitação real ainda existente, sem antecipar como erro aquilo que pertence a uma tarefa posterior;
5. forneça ao usuário os comandos sugeridos para revisar e fazer um único commit da tarefa, incluindo `git status`, `git diff --check`, `git diff`, `git add` com os caminhos exatos e `git commit -m "..."`;
6. não execute os comandos apresentados.

Na tarefa 1, inclua também instruções para o usuário criar um repositório vazio no GitHub, inicializar o Git local com branch `main`, cadastrar o remoto e enviar o primeiro commit. Nas tarefas seguintes, não repita a configuração do repositório.

Cada tarefa abaixo corresponde a exatamente um commit. O agente pode fazer várias alterações e testes dentro da tarefa, mas deve entregar um estado coerente e revisável.

## 6. Tarefas

### Tarefa 1 — Estrutura inicial do projeto e instruções do repositório

Crie a estrutura básica do projeto, `.gitignore`, `README.md`, `Makefile` inicial e arquivos mínimos para compilar um executável C++20 ainda simples. Prepare diretórios para código, testes, scripts, configurações, instâncias e resultados. Crie também `docs/decisoes_implementacao.md` com uma introdução curta e uma seção inicial informando que ainda não há decisões registradas. Esse arquivo será cumulativo: cada tarefa posterior deve atualizá-lo somente quando tomar ou revisar uma decisão de implementação não determinada diretamente pelo TP3, pelas fontes ou pelo código anterior. Ignore em Git o conteúdo bruto de `instances/source/`, preservando um arquivo de instruções nesse diretório. O README deve registrar o problema estudado, os seis nomes executáveis (`Hbase`, `Hext`, `Hint`, `Hcomb`, `Haleat` e `RLS-f7`), as fontes acadêmicas principais e o fato de que `Haleat` é apenas controle auxiliar.

Garanta que `make` e `make test` funcionem desde este primeiro estado. Ao final, oriente o usuário a criar o repositório GitHub e fazer o primeiro commit, sem executar Git.

Mensagem sugerida: `chore: cria estrutura inicial do projeto`.

### Tarefa 2 — Modelo da instância, leitura e expansão das demandas

Implemente as estruturas simples para tipo de peça, cópia individual e instância. Implemente o leitor do formato unificado da 2DPackLib: quantidade de tipos; dimensões `W H`; e, para cada tipo, `id wi hi di bi pi`. Para este trabalho, use largura, altura e demanda e preserve os demais campos lidos quando forem úteis para diagnóstico.

Valide dimensões e demandas positivas, IDs e quantidade de linhas. Expanda cada demanda em cópias com identificadores únicos e vínculo com o tipo original. Acrescente testes com pequenas instâncias válidas e inválidas criadas em `tests/data/`.

Mensagem sugerida: `feat: implementa leitura e expansão das instâncias`.

### Tarefa 3 — Catálogo das instâncias e divisão piloto/final

Partindo dos arquivos fornecidos em `instances/source/`, implemente um script que reconheça e catalogue `A`, `BENG` e `CLASS`, sem renomear os originais. Gere manifestos versionados com caminho, família, identificador, número de tipos, total de cópias, dimensões da chapa, classe, tamanho e réplica quando aplicáveis.

O manifesto do piloto deve conter exatamente:

- cinco das 43 instâncias `A`, ordenadas pelo total de cópias e depois pelo identificador, nas posições 1, 11, 22, 33 e 43;
- cinco `CLASS` de tamanho 60 e réplica 02, das classes 1, 3, 5, 7 e 9.

O manifesto final deve conter exatamente 153 instâncias, sem interseção com o piloto:

- as 38 instâncias `A` restantes;
- as dez `BENG`;
- as 100 `CLASS` das réplicas 01 e 06, nas dez classes e nos tamanhos 20, 40, 60, 80 e 100;
- cinco `CLASS` de tamanho 60 e réplica 02, das classes 2, 4, 6, 8 e 10.

O script deve falhar com mensagem clara se arquivos estiverem ausentes, duplicados ou fora do formato. Acrescente uma verificação automática das contagens e da disjunção entre piloto e conjunto final. Não execute esta tarefa com dados inventados.

Mensagem sugerida: `data: cataloga instâncias do piloto e benchmark final`.

### Tarefa 4 — Modelo de solução e verificador independente

Implemente as estruturas de posicionamento, chapa e solução. Cada cópia deve registrar chapa, coordenadas, dimensões usadas e orientação. Defina um formato textual ou CSV simples para salvar uma solução completa quando solicitado.

Implemente um verificador independente que confira atendimento exato das demandas, unicidade das cópias, orientação permitida, contenção e ausência de sobreposição. Contato por bordas deve ser permitido. Crie testes positivos e negativos específicos para cada regra.

Mensagem sugerida: `feat: adiciona modelo e verificador de soluções`.

### Tarefa 5 — Geometria comum e decodificador inferior-esquerdo por pontos de canto

Implemente as operações geométricas comuns e o decodificador usado pelas quatro configurações propostas. Para uma sequência, examine pontos de canto válidos e as duas orientações; priorize menor `y` e depois menor `x`, com desempates determinísticos. Remova pontos inválidos, redundantes e duplicados. Se uma peça não puder ser posicionada, marque-a como rejeitada e continue processando a sequência.

O resultado deve preservar a ordem, as peças colocadas, as rejeitadas, a primeira rejeitada, a área rejeitada e os dados necessários às buscas posteriores. Teste rotações, cantos, bloqueios, rejeição e desempates.

Mensagem sugerida: `feat: implementa decodificador inferior esquerdo`.

### Tarefa 6 — Empacotador-base com oito tentativas

Implemente `EmpacotaBase`. Se a área total superar `W * H`, encerre a chamada com o resultado inviável correspondente, sem executar as oito tentativas. Caso contrário, avalie:

- uma sequência decrescente por área, maior lado, menor lado e identificador;
- seis sequências parcialmente aleatórias, escolhendo a próxima peça entre as `ceil(sqrt(|S|))` maiores restantes;
- uma sequência anterior atualizada ou, quando ela não existir, mais uma tentativa parcialmente aleatória.

Se nenhuma tentativa for completa, selecione a menor área rejeitada e depois o menor número de rejeições, mantendo desempates finais determinísticos. Retorne também os resultados individuais das tentativas para `Hext`. Adicione testes para as oito tentativas e os critérios de escolha.

Mensagem sugerida: `feat: implementa empacotador base multissequência`.

### Tarefa 7 — Solução inicial construtiva

Implemente a construção inicial comum às quatro configurações. Ordene as cópias por área, maior lado, menor lado e identificador, todos em ordem decrescente. Para cada peça, escolha a chapa viável que deixe a menor folga de área e use o posicionamento inferior-esquerdo; abra nova chapa quando nenhuma existente puder recebê-la.

Teste factibilidade, desempates, abertura de chapas e casos em que apenas a rotação permite inserir uma peça.

Mensagem sugerida: `feat: implementa construção da solução inicial`.

### Tarefa 8 — Limites inferiores e desvio percentual

Implemente o limite por área e o limite de Dell'Amico, Martello e Vigo para a variante com rotação. Consulte a fonte original citada no TP3 para não reconstruir a fórmula por memória. Defina `LBref` como o maior dos dois limites e calcule o desvio `100 * (K - LBref) / LBref`.

Crie testes com exemplos pequenos calculáveis manualmente e, quando houver valores publicados ou uma implementação confiável para comparação, faça testes de regressão. Documente no README a referência e quaisquer cuidados de interpretação. Não substitua o limite de Dell'Amico apenas pelo limite de área caso a implementação seja difícil.

Mensagem sugerida: `feat: implementa limites inferiores de referência`.

### Tarefa 9 — Estado de reparo, inviabilidade e remoção de chapa

Implemente o estado usado na busca externa, permitindo chapas temporariamente inviáveis. Compare esses estados lexicograficamente por excesso total de área, área rejeitada, quantidade de chapas inviáveis e quantidade de peças rejeitadas.

Implemente a remoção da chapa menos ocupada e a redistribuição inicial de suas peças, das maiores para as menores, entre as chapas restantes. Defina os desempates de forma determinística e teste conservação de peças, seleção da chapa e comparação dos estados.

Mensagem sugerida: `feat: adiciona estado inviável e eliminação de chapa`.

### Tarefa 10 — VND e vizinhanças da busca externa

Implemente o VND com realocação de uma peça, troca entre duas chapas e realocação de um par. Em cada vizinhança, amostre sem reposição até `ceil(sqrt(T))` peças-base; avalie todos os candidatos amostrados; aceite a melhor melhoria estrita; e retorne à primeira vizinhança após melhorar. Reempacote somente as chapas alteradas.

Siga as regras do TP3 para escolher origem, receptora, parceiro de troca e segunda peça do par. Comece com seleção uniforme das peças-base. Crie testes em que cada vizinhança produz uma melhoria conhecida e confirme que nenhum movimento perde ou duplica peças.

Mensagem sugerida: `feat: implementa VND da busca externa`.

### Tarefa 11 — VNS, perturbações e configuração Hbase

Implemente as perturbações da VNS, redistribuindo peças de duas ou mais chapas e reiniciando o VND. Mantenha quantidade de chapas perturbadas, reinícios e orçamento de reparo em uma configuração explícita que possa ser calibrada no piloto.

Integre construção inicial, tentativa de reduzir `K` para `K - 1`, VND, perturbação, aceitação e parada para formar `Hbase`, conforme o Algoritmo 1 do TP3. Reinicie a tentativa de redução quando uma solução factível com menos uma chapa for obtida; pare ao atingir `LBref`, o limite de CPU ou quando a redução não puder ser reparada dentro do orçamento. Teste o fluxo em instâncias pequenas.

Mensagem sugerida: `feat: implementa Hbase com VNS e VND`.

### Tarefa 12 — Orientação externa Hext

Implemente o histórico indexado pela composição da chapa e pelo tipo de peça. Para um conjunto de oito tentativas cuja área cabe, mas que falhou completamente, conte uma única vez as oportunidades `O` e rejeições `F`. Use `C = F / max(1, O)` e peso `1 + C` para amostrar peças-base sem reposição.

O histórico deve ser reiniciado a cada nova tentativa de reduzir `K` para `K - 1`. Consultas posteriores não podem contabilizar novamente o mesmo conjunto de tentativas. Registre movimentos orientados e melhorias aceitas. Integre o módulo a `Hbase` para formar `Hext` e teste contagem única, pesos e reinício.

Mensagem sugerida: `feat: implementa orientação externa Hext`.

### Tarefa 13 — Orientação interna Hint

Implemente a busca interna iniciada pela melhor sequência incompleta das oito tentativas. Localize a primeira peça rejeitada e examine até oito posições anteriores, da mais próxima à mais distante. Procure primeiro a primeira inserção que melhore área rejeitada e, em empate, número de rejeições; se necessário, procure trocas seguindo a mesma ordem.

Após uma melhoria, reinicie com a nova primeira rejeição. Encerre ao completar o empacotamento, atingir 16 decodificações adicionais ou não encontrar melhoria. Registre ativações, decodificações extras, melhorias e empacotamentos completos. Integre seleção externa uniforme e esse empacotador para formar `Hint`. Teste a ordem de busca e o limite de avaliações.

Mensagem sugerida: `feat: implementa orientação interna Hint`.

### Tarefa 14 — Controle auxiliar Haleat

Implemente `Haleat` com os mesmos componentes e orçamento adicional de `Hint`, mas escolhendo aleatoriamente a peça e as posições examinadas. Preserve todo o restante para que a comparação meça a orientação pela primeira rejeição, e não apenas o esforço adicional.

Registre as mesmas métricas internas de `Hint` e crie um teste que demonstre que, com a mesma semente, a execução é reproduzível. Mantenha `Haleat` identificada no código e nos resultados como controle auxiliar.

Mensagem sugerida: `feat: adiciona controle auxiliar Haleat`.

### Tarefa 15 — Configuração combinada Hcomb

Integre a seleção ponderada de `Hext` e a busca interna de `Hint`. Quando as oito tentativas básicas falharem sem excesso de área, atualize o histórico uma única vez e só então execute a busca interna. As decodificações adicionais não devem alterar o histórico.

Reutilize os componentes existentes sem duplicar algoritmos. Adicione testes de integração que comprovem a ordem dos eventos, a contagem única e a ausência de atualização do histórico pelas tentativas extras.

Mensagem sugerida: `feat: integra mecanismos na configuração Hcomb`.

### Tarefa 16 — Decodificador IBL e função f7 da RLS

Implemente separadamente o decodificador Improved Bottom Left descrito no artigo da RLS. A representação é uma permutação com repetições; o sinal escolhe a orientação. Para cada peça, comece no canto superior direito da chapa corrente, mova para baixo e para a esquerda até estabilizar, dando prioridade ao movimento para baixo. Se não couber, abra uma nova chapa e coloque-a no canto inferior esquerdo. Corrija a orientação quando a escolhida não couber nem em uma chapa vazia, conforme o artigo.

Implemente a área sob o perfil superior da última chapa e `f7`, garantindo que qualquer redução de `K` tenha prioridade. Teste o decodificador, o perfil e valores de `f7` calculados manualmente.

Mensagem sugerida: `feat: implementa IBL e função f7`.

### Tarefa 17 — Busca local aleatorizada RLS-f7

Implemente a inicialização por permutação aleatória com repetições e sinais. A cada iteração, escolha uma posição uniformemente. Com probabilidade `1/2`, tente encontrar em até `10 * T` sorteios outra posição com valor assinado diferente e faça a troca; se a troca não for usada, inverta o sinal. Aceite o candidato quando `f7` não aumentar.

Pare por tempo de CPU, por `LBref` ou pelo teto publicado de `100000000` avaliações da função objetivo. Registre avaliações, `K`, `f7`, tempo até a melhor solução e evolução nos tempos de interesse. Teste movimentos, aceitação, limite de avaliações e reprodutibilidade.

Mensagem sugerida: `feat: implementa heurística RLS-f7`.

### Tarefa 18 — Executável comum, configuração e registro de resultados

Crie uma interface de linha de comando única para executar uma instância e um método, informando configuração, semente, limite de CPU, diretório de saída e opção de salvar a solução. Valide argumentos e imprima mensagens de erro úteis.

Padronize um CSV por execução com, no mínimo: versão do formato, instância, família, método, semente, parâmetros congelados, `LBref`, `K`, desvio, tempo total, tempo até a melhor solução, alcance do limite, avaliações e métricas internas aplicáveis. Registre também o melhor `K` e o desvio nos marcos de 0,1; 1; 5; 10; 30 e 60 segundos. Toda solução final deve ser validada antes de o registro ser aceito.

Mensagem sugerida: `feat: adiciona interface e registro dos experimentos`.

### Tarefa 19 — Testes integrados das seis configurações

Monte um conjunto pequeno de instâncias de teste para executar `Hbase`, `Hext`, `Hint`, `Hcomb`, `Haleat` e `RLS-f7` com orçamentos curtos. Verifique factibilidade, determinismo com semente fixa, conservação das peças, formato dos resultados, critérios de parada e comportamento quando `LBref` é atingido.

Adicione um alvo como `make integration-test` e corrija as falhas encontradas sem começar ainda os experimentos formais.

Mensagem sugerida: `test: cobre integração de todas as configurações`.

### Tarefa 20 — Orquestração retomável e protocolo experimental

Implemente scripts para executar uma lista de instâncias, métodos e sementes sequencialmente. Uma execução completa e validada deve ser reconhecida e pulada ao retomar; arquivo parcial ou inválido deve ser refeito sem apagar outros resultados. Grave primeiro em arquivo temporário e mova para o nome final apenas depois da validação.

Versione as dez sementes comuns `1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010`. Registre compilador, opções de compilação, kernel, CPU, RAM, data e hash ou identificação da configuração. Garanta que somente um processo seja executado de cada vez e ofereça modos explícitos `calibration`, `pilot`, `preflight` e `final`.

Mensagem sugerida: `feat: cria orquestração reproduzível dos experimentos`.

### Tarefa 21 — Calibração e congelamento dos parâmetros da arquitetura

Antes de observar resultados do benchmark final, defina e documente uma grade pequena e justificável para perturbações, reinícios e orçamento de reparo. Execute uma calibração de orçamento reduzido apenas nas dez instâncias-piloto. Use o mesmo conjunto de opções para as quatro configurações propostas e evite uma grade grande que favoreça sobreajuste.

Analise qualidade e tempo, escolha uma configuração comum e grave-a em um arquivo imutável de configuração usado pelas próximas tarefas. Salve resultados e uma nota curta com grade, critério e escolha. Não use as 153 instâncias finais.

Mensagem sugerida: `experiment: calibra e congela parâmetros da busca`.

### Tarefa 22 — Piloto formal e seleção de H*

Execute `Hbase`, `Hext`, `Hint` e `Hcomb` nas dez instâncias-piloto, com as dez sementes comuns, 60 segundos de CPU e parâmetros congelados. São esperadas 400 execuções válidas. Valide todas as soluções e confira a completude da matriz antes de analisar.

Selecione `H*` pelo menor desvio médio para `LBref`; em empate, use maior alcance do limite e depois menor tempo mediano até o melhor valor. Grave a identidade de `H*`, os resultados brutos, o resumo do piloto e um arquivo de congelamento que as tarefas posteriores não possam alterar silenciosamente.

Mensagem sugerida: `experiment: executa piloto e seleciona H estrela`.

### Tarefa 23 — Pré-execução completa do benchmark final

Execute uma passagem curta sobre as 153 instâncias e os seis métodos, com uma semente e limite pequeno, apenas para encontrar problemas de leitura, memória, validação, nomes de arquivos e retomada. Essa passagem não integra os resultados científicos finais e deve ficar em `results/preflight/`.

Confirme as 153 instâncias, os seis métodos, a inexistência de instâncias-piloto e a capacidade de retomar. Corrija qualquer falha encontrada antes das execuções longas.

Mensagem sugerida: `test: valida matriz completa do benchmark`.

### Tarefa 24 — Benchmark final da família A

Execute os seis métodos nas 38 instâncias `A` do conjunto final, com dez sementes e 60 segundos de CPU. São esperadas `38 * 6 * 10 = 2280` execuções válidas, aproximadamente 38 horas de CPU se nenhuma terminar cedo.

Use retomada, um processo por vez e os arquivos congelados. Valide cada solução, confira a matriz completa e gere um resumo de integridade da família. Não faça conclusões estatísticas globais nesta tarefa.

Mensagem sugerida: `experiment: executa benchmark final da família A`.

### Tarefa 25 — Benchmark final da família BENG

Execute os seis métodos nas dez instâncias `BENG`, com dez sementes e 60 segundos de CPU. São esperadas 600 execuções válidas, aproximadamente dez horas de CPU se nenhuma terminar cedo.

Siga o mesmo protocolo da tarefa anterior, valide as soluções e gere o resumo de integridade da família.

Mensagem sugerida: `experiment: executa benchmark final da família BENG`.

### Tarefa 26 — Benchmark final da família CLASS

Execute os seis métodos nas 105 instâncias `CLASS` do conjunto final, com dez sementes e 60 segundos de CPU. São esperadas 6300 execuções válidas, aproximadamente 105 horas de CPU se nenhuma terminar cedo.

Esta tarefa é longa e deve usar retomada. Não mantenha o agente bloqueado sem atualizações durante toda a execução: inicie e acompanhe o processo, informe progresso significativo e continue até completar ou até existir uma falha concreta que exija intervenção. Ao final, valide a matriz e gere o resumo de integridade da família.

Mensagem sugerida: `experiment: executa benchmark final da família CLASS`.

### Tarefa 27 — Consolidação e auditoria dos resultados finais

Consolide os três conjuntos sem alterar os CSVs brutos. Confirme exatamente 9180 execuções finais: 153 instâncias, 6 métodos e 10 sementes. Verifique chaves duplicadas, campos ausentes, sementes comuns, tempo, parâmetros, validade das soluções, `LBref`, instâncias indevidas e correspondência com os arquivos congelados.

Produza um relatório legível de auditoria e faça a etapa falhar se qualquer inconsistência permanecer. Separe claramente piloto, preflight e benchmark final.

Mensagem sugerida: `data: consolida e audita resultados finais`.

### Tarefa 28 — Análise estatística, tabelas e figura

Implemente scripts de análise em Python, com dependências declaradas e código simples. Faça 10000 reamostragens para intervalos de confiança de 95%, primeiro reamostrando instâncias de forma estratificada para preservar as quantidades de `A`, `BENG` e `CLASS`, e depois as execuções pareadas pelas sementes. Use a instância como unidade principal.

Gere:

- tabela 1 com método, média de `K`, desvio mediano, alcance de `LBref` e tempo mediano até a melhor solução, no conjunto completo e separadamente em `A`;
- tabela 2 com cada hipótese, métodos, diferença média de `K`, intervalo de confiança, vitórias–empates–derrotas, métricas diagnósticas e conclusão;
- figura do desvio médio em 0,1; 1; 5; 10; 30 e 60 segundos para `Hbase`, `Hext`, `Hint`, `Hcomb` e `RLS-f7`.

Aplique exatamente as comparações e regras do TP3:

- `K(Hbase) - K(Hext)` para a orientação externa;
- `K(Hbase) - K(Hint)` e `K(Haleat) - K(Hint)` para a orientação interna;
- `K(Hbase) - K(Hcomb)`, `K(Hext) - K(Hcomb)` e `K(Hint) - K(Hcomb)` para a combinação;
- `K(RLS-f7) - K(H*)` para a competitividade da configuração escolhida.

Uma comparação é favorável ao método da direita quando o limite inferior do intervalo é positivo; é desfavorável quando o limite superior é menor ou igual a zero; nos demais casos, é inconclusiva. Para a hipótese da combinação, siga a regra conjunta descrita no TP3. Inclua as métricas específicas de `Hext` e `Hint` previstas no projeto. Gere CSVs processados e versões da figura em PNG e PDF.

Mensagem sugerida: `analysis: gera estatísticas tabelas e figura finais`.

### Tarefa 29 — Auditoria final de código e reprodutibilidade

Revise o projeto completo procurando inconsistências com o TP3, duplicação desnecessária, comentários excessivos, parâmetros não congelados, caminhos absolutos, sementes implícitas e arquivos temporários. Execute todos os testes e uma execução curta representativa de cada método. Não altere resultados científicos já validados, salvo para corrigir um erro comprovado; nesse caso, explique quais tarefas experimentais precisam ser refeitas.

Complete o README com dependências, compilação, testes, organização, preparação manual das instâncias, comandos do piloto e benchmark, retomada, validação e reprodução das análises. Registre versões do ambiente final e um inventário dos artefatos destinados ao TA e ao TE.

Mensagem sugerida: `docs: finaliza reprodução do estudo experimental`.

## 7. Formato obrigatório da resposta do agente

Ao trabalhar na tarefa selecionada, responda durante a execução com atualizações curtas apenas quando houver progresso ou descoberta relevante. Na resposta final, use esta estrutura:

1. **Resultado da tarefa** — o que ficou pronto.
2. **Arquivos** — caminhos criados ou alterados.
3. **Verificação** — comandos de compilação/teste executados e resultado.
4. **Observações** — limitações reais ou decisões relevantes; omita se não houver.
5. **Commit manual** — comandos exatos para o usuário revisar e criar o único commit da tarefa. Não execute esses comandos.

Não avance para a próxima tarefa. Não inclua mudanças pertencentes a tarefas futuras apenas porque seriam convenientes.

---

**TAREFA A EXECUTAR:** 18 e 19 (faça uma por vez: por exemplo, finja que você só tem que fazer a 18, depois de concluir, ao invés de me gerar uma resposta, passe para a próxima - só me dê uma resposta condensando o que seria a resposta para cada uma delas individualmente. Além disso pode fazer um commit só para todas essas tarefas)
