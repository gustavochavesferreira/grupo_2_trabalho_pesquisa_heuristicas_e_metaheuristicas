# Piloto reduzido para a V1 do TA

Na raiz: `python3 scripts/piloto_v1.py`.

São A14 (809 peças), A23 (248 peças) e CLASS 3/60/02, 7/60/02 e 9/60/02
(60 peças cada), escolhidas entre
as instâncias-piloto que antes não atingiram LBref. Esta seleção intencional de
casos difíceis para as propostas não representa a distribuição do benchmark.
Hbase/Hext/Hint/Hcomb, sementes comuns 1001, 1002, 1003: 60 execuções, até
60 segundos de CPU por execução. Mantém a configuração congelada v2.

Teto nominal de 60 minutos de CPU mais auditoria. A chamada tem por padrão
teto de 75 minutos de parede, alterável com --max-minutos. Se expirar, retorna
124 e preserva completos; repita o comando para retomar. Ctrl+C também permite
retomada. Mantenha a máquina sem suspensão e não rode o piloto formal em paralelo.

O comando mantém o bloco original de 36 em results/ta_v1/ e acrescenta 24 em
results/ta_v1_extra/ (A23 e CLASS 3). Contratos antigos não são alterados e os
resultados completos originais são reaproveitados após validação. Cada bloco tem
resumo.csv, integridade.json e calibration/congelada_v2/ com dados e logs.
A tabela das cinco instâncias, com 20 linhas, será results/ta_v1/resumo_ampliado.csv;
a comprovação completa é integridade_ampliado.json no mesmo diretório.
Os ambientes dos dois blocos precisam coincidir para consolidar. O nome interno calibration é um modo
flexível do orquestrador existente, não afirmação de calibração ou piloto formal.
O resumo ampliado só é publicado após validar os dois blocos, com 60 geometrias.

Na apresentação rotular: "Piloto preliminar: 5 instâncias, 3 sementes por método,
até 60 s de CPU. H* e benchmark final ainda pendentes." Não confirma/refuta as
hipóteses oficiais nem substitui o piloto 10×4×10. Não executa RLS-f7, não cria
H* e não altera selos oficiais. Resultados não devem ser apresentados como
comparação com a literatura ou como resultado das 153 instâncias finais.

Planejamento sem executar: `python3 scripts/piloto_v1.py --planejar`.
Somente auditoria/análise: `python3 scripts/piloto_v1.py --analisar`.

O parcial do piloto formal foi retirado da área ativa, a pedido do usuário,
com a trava global livre. Backup recuperável: /tmp/tp3_piloto_parcial.qedoXN.
Se o piloto formal for executado depois, começará novamente. Não misture os
resultados reduzidos com os oficiais sem um protocolo explícito de incorporação.

Se o comando de 36 execuções já estiver rodando quando o arquivo for atualizado,
deixe-o terminar e execute o comando novamente. O novo processo pula os 36
completos e executa os 24 adicionais. Não abra o novo lote em paralelo.
