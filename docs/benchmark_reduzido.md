# Benchmark reduzido para o TA

Comando: `python3 scripts/benchmark_reduzido.py`. Não exige H* e não a seleciona.
Configuração congelada v2, seis métodos, sementes 1001–1003, até 60 s de CPU.

Seleção determinística no manifesto final: ordenar A e BENG por cópias e depois
identificador; escolher índices n//3 e 2n//3, começando em zero. Acrescentar CLASS
3 e 7, tamanho 100, réplica 01. Isso dá A36, A32, BENG03, BENG05,
cl_03_100_01 e cl_07_100_01. São dois casos de cada família, sem interseção com
o piloto; não se escolhem casos porque favorecem um método. A seleção é pequena
e não pretende representar toda a dificuldade ou distribuição do benchmark.

108 execuções: teto nominal de 108 minutos de CPU, mais compilação e auditoria.
O teto de parede padrão da chamada é 120 minutos. --max-minutos altera apenas
o teto da chamada, nunca os 60 segundos de CPU por execução. No Linux, o prazo
interrompe o filho atual; retorna 124. Ctrl+C retorna 130. Repita o comando para
retomar os completos, sempre na mesma máquina/código/ambiente/caminho.

Saídas em results/benchmark_reduzido/congelada_v2/: contrato.json, config.cfg,
execucoes/ com resultados/soluções/recibos/logs, integridade.json e
tabela_comparacao.csv. .pendentes/ guarda tentativas incompletas e não integra
a tabela. Publicação ocorre após validação, com renomeação de diretório.
Resultados publicados corrompidos causam erro e são preservados para inspeção.

--planejar não compila ou executa métodos. --analisar exige as 108 execuções,
reaudita geometrias, configuração e recibos e recria a tabela geral. Os hashes
do executor e ambiente participam do contrato. Não altere o script durante o lote.

A tabela tem uma linha por método e agrega igualmente instâncias e sementes.
As famílias têm peso igual nesta seleção, diferente da matriz final 38/10/105.
Não se calculam decisões confirmatórias ou H* a partir deste subconjunto.
Tempo de melhor K não significa tempo até o fim: ambos são apresentados.
As unidades de avaliação de RLS e arquitetura são diferentes.

Compartilhe com colegas a pasta completa, não apenas a tabela; ela contém o
ambiente e a comprovação dos resultados. Não misture ou retome blocos de máquinas
diferentes. Não há alteração ou aproveitamento automático dos pilotos anteriores.
