# Execução individual e resultados — versão 1

Na raiz, compile com `make`. `./bin/tp3 --ajuda` lista a interface.

```bash
./bin/tp3 --instancia tests/data/valida.txt --metodo Hcomb \
  --config config/congelada_v2.cfg --semente 1001 --cpu 1 \
  --saida results/teste --salvar-solucao
```

Os seis argumentos com valor são obrigatórios. Os métodos são `Hbase`, `Hext`,
`Hint`, `Hcomb`, `Haleat` e `RLS-f7`, com essa grafia. A semente é um inteiro de
0 a 4294967295. CPU é um número finito positivo em segundos, com ponto decimal;
notação científica é aceita. `--salvar-solucao` é uma opção sem valor. Sem
argumentos, `--ajuda` ou `--help`, o programa mostra apresentação e ajuda.
Opções desconhecidas/repetidas, valores incompletos ou arquivos inválidos falham
com diagnóstico em stderr e código 1. Expirar antes da primeira solução completa
retorna código 3 e não cria um resultado. Sucesso retorna 0.

O limite mede CPU do processo desde o início do método: construção/inicialização,
limites inferiores, busca, validações internas e coleta da evolução. Leitura da
instância/configuração e gravação do CSV ficam fora da medição dos métodos,
preservando a fronteira de cronometragem das Tarefas 11/17. As checagens são
cooperativas: operações atômicas podem terminar após o prazo, e o tempo efetivo
é registrado. Há nova validação independente antes da publicação do registro.

## Configuração

O arquivo tem uma chave por linha, no formato `chave=valor`. Espaços externos,
linhas vazias e comentários iniciados por `#` são aceitos. Todas as chaves são
obrigatórias; chaves extras/repetidas são rejeitadas.

```text
versao=1
id=congelada_v2
estado=congelado
chapas_perturbadas=2
max_reinicios=50000
max_avaliacoes_reparo=1000000
rls_max_avaliacoes=100000000
```

`id` começa com letra/número ASCII e usa letras, números, `_`, `-` ou `.`.
`estado` declara `provisorio` ou `congelado`; o programa não calibra nem congela
parâmetros. A configuração ativa é config/congelada_v2.cfg, protegida por selo
SHA-256. config/provisoria.cfg permanece apenas como fixture dos testes automatizados.
Cada registro inclui todos
os valores efetivamente carregados, além do caminho, ID e estado da configuração.

`chapas_perturbadas` deve ser pelo menos 2. Reinícios e avaliações de reparo
podem ser zero. `rls_max_avaliacoes` fica entre 1 e 100000000, contando a inicial;
valores menores destinam-se a testes. As oito tentativas básicas e o teto de
16 decodificações internas são fixos pelo TP3, sem opções para alterá-los.

## Arquivos de saída

No diretório indicado, o resultado é
`<instancia>__<metodo>__<semente>__<config_id>.csv`. Com a opção de salvar,
os posicionamentos ficam no arquivo de mesmo prefixo e sufixo `.solucao.csv`,
no [formato de solução existente](formato_solucao.md). Ambos são recusados se
já existirem, inclusive links simbólicos. Use outro diretório para repetir uma
execução. A CLI individual não faz retomada nem coordena processos; use o
[orquestrador de lotes](experimentos.md) para isso. Uma falha de escrita retorna erro e o arquivo não deve ser tratado
como execução concluída.

O identificador é o nome da instância sem extensão. Caracteres não ASCII,
espaços e pontuação são substituídos por `_` somente no nome da saída; os campos
CSV preservam o nome e o caminho originais. A família é reconhecida pelo mesmo
padrão de nomes do catálogo para A/BENG/CLASS; arquivos de teste ou nomes fora
desse padrão recebem `OUTRA`. A inferência não altera o catálogo ou a seleção.

## CSV de resultado

Um cabeçalho e uma linha por execução, UTF-8, separados por vírgula, com aspas
duplas escapadas. Reais usam ponto e precisão suficiente para recuperar `double`.
`f7` é um inteiro decimal exato, inclusive acima de 64 bits. Booleanos usam 0/1.
Métricas não aplicáveis ficam vazias; zero significa uma métrica aplicável que
não registrou eventos.

| Grupo | Campos |
|---|---|
| Identificação | `versao`, `instancia`, `caminho_instancia`, `familia`, `metodo`, `controle_auxiliar`, `semente` |
| Configuração | `config_id`, `config_estado`, `config_arquivo`, `chapas_perturbadas`, `max_reinicios`, `max_avaliacoes_reparo`, `rls_max_avaliacoes`, `tentativas_basicas`, `max_decodificacoes_extras`, `limite_cpu` |
| Qualidade | `LBarea`, `LBdmv`, `LBref`, `K`, `desvio`, `alcancou_lb` |
| Tempo/parada | `tempo_total`, `tempo_melhor`, `limite_cpu_atingido`, `motivo_parada` |
| Esforço | `avaliacoes`, `unidade_avaliacoes`, `tentativas_reducao`, `reducoes_aceitas`, `perturbacoes` |
| Hext/Hcomb | `historico_atualizacoes`, `historico_reinicios`, `movimentos_orientados`, `melhorias_orientadas` |
| Hint/Hcomb/Haleat | `ativacoes_internas`, `decodificacoes_extras`, `melhorias_internas`, `empacotamentos_completos` |
| RLS-f7 | `f7`, `area_perfil`, `trocas`, `inversoes`, `aceitos_rls`, `melhorias_rls` |
| Evolução | pares `K_<t>`, `desvio_<t>` para sufixos `0_1`, `1`, `5`, `10`, `30`, `60` |
| Validação/solução | `validada`, `solucao_arquivo` |

Somente Haleat tem `controle_auxiliar=1`. Todos os parâmetros de configuração
são registrados, inclusive os do componente não usado pelo método. Os campos
de mecanismos e `tentativas_basicas` respeitam sua aplicabilidade. Avaliações
significam candidatos externos para a arquitetura (`candidato_externo`) e
avaliações completas da função objetivo para a RLS (`f7`); não são uma unidade
de esforço intercambiável. O esforço interno aparece em `decodificacoes_extras`.

`tempo_melhor` é o primeiro instante em que o menor K foi obtido. `alcancou_lb`
indica K=LBref. `limite_cpu_atingido` compara o tempo efetivo com o orçamento,
independentemente da prioridade dada à parada por LBref. Motivos possíveis:
`limite_inferior`, `limite_cpu`, `orcamento_reparo` (arquitetura) e
`limite_avaliacoes` (RLS). O registro exige solução válida e limites, tempos,
evolução e motivo de parada consistentes; a RLS também confere perfil e f7.

Os marcos usam a última solução validada disponível até o instante pedido.
Antes da construção completa, os dois campos ficam vazios. Depois de parada
antecipada, conserva-se o último K, sem executar espera artificial. Melhorias
futuras nunca são atribuídas a instantes anteriores. `solucao_arquivo` é relativo
ao diretório do resultado e fica vazio quando a exportação não foi solicitada.

## Testes integrados

`make integration-test` executa os seis métodos em casos pequenos e com
orçamentos curtos. A matriz C++ usa seis instâncias, duas sementes e duas
repetições (144 execuções), validação independente, conservação, reprodução e
parada inicial por LBref; outras seis execuções exercitam CPU real. Os casos
dirigidos estão em `tests/data/integracao/`, junto de instruções.

O teste da CLI repete quatro casos nos seis métodos (48 execuções), lê o CSV e
reconstrói cada solução exportada. Um verificador Python independente confere
cópias/tipos, demandas, orientação, contenção e sobreposição, além de perfil/f7
por soma de colunas. Outras 12 chamadas cobrem CPU com e sem incumbente.
Reprodução compara soluções e métricas de operações; tempos medidos não são
exigidos iguais. As execuções de cada teste são sequenciais e seus arquivos
ficam em diretórios temporários, fora dos resultados científicos.
