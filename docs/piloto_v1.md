# Piloto reduzido para a V1 do TA

Na raiz: `python3 scripts/piloto_v1.py`.

São A14 (809 peças) e CLASS 7/60/02 e 9/60/02 (60 peças cada), escolhidas entre
as instâncias-piloto que antes não atingiram LBref. Esta seleção intencional de
casos difíceis para as propostas não representa a distribuição do benchmark.
Hbase/Hext/Hint/Hcomb, sementes comuns 1001, 1002, 1003: 36 execuções, até
60 segundos de CPU por execução. Mantém a configuração congelada v2.

Teto nominal de 36 minutos de CPU mais auditoria. A chamada tem por padrão
teto de 45 minutos de parede, alterável com --max-minutos. Se expirar, retorna
124 e preserva completos; repita o comando para retomar. Ctrl+C também permite
retomada. Mantenha a máquina sem suspensão e não rode o piloto formal em paralelo.

Saídas em results/ta_v1/: resumo.csv (12 linhas, por instância/método),
integridade.json e calibration/congelada_v2/ com contrato, ambiente e 36
conjuntos de resultado/solução/recibo/logs. O nome interno calibration é um modo
flexível do orquestrador existente, não afirmação de calibração ou piloto formal.
O resumo só é publicado após conferir a matriz completa e as 36 geometrias.

Na apresentação rotular: "Piloto preliminar: 3 instâncias, 3 sementes por método,
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
