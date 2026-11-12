# Pré-execução técnica da Tarefa 23

Por solicitação do usuário, esta etapa é executada depois da calibração e antes
do piloto formal. O usuário autorizou o Ryzen 3 conectado para as etapas locais;
a máquina real permanece identificada no contrato, sem compensação artificial
no limite de CPU. A mudança de ordem não autoriza recalibrar usando dados finais.

Protocolo: 153 instâncias do manifesto final, seis métodos, somente semente 1001,
três segundos de CPU por execução, configuração congelada_v1. São 918 execuções,
com 38 instâncias A, 10 BENG e 105 CLASS, sem interseção com o piloto. O limite
curto admite a construção inicial dos casos maiores e não substitui os 60
segundos previstos para piloto e benchmark formais.

```bash
python3 scripts/verificar_congelamento.py
python3 scripts/executar_experimentos.py --modo preflight \
  --config config/congelada_v1.cfg --sementes 1001 --cpu 3 --planejar
python3 scripts/executar_experimentos.py --modo preflight \
  --config config/congelada_v1.cfg --sementes 1001 --cpu 3
python3 scripts/auditar_preflight.py --verificar-retomada
```

Repetir o comando de execução retoma o mesmo lote. O lote, CSVs, soluções,
contrato, ambiente e logs ficam em results/preflight/congelada_v1/. O plano,
o relatório de integridade e a comprovação da retomada ficam na pasta superior.
Os dados dessa passagem têm finalidade exclusivamente técnica. Não se geram
rankings, comparação de K/desvios, seleção de H* ou novos parâmetros a partir
deles. A validação precisa ler esses campos para conferir consistência, sem
usá-los para escolher métodos.

A auditoria exige a matriz completa e sem duplicações/excedentes, hashes de
manifestos/configuração/sementes e o mesmo executável. Cada recibo, CSV e solução
é novamente verificado, incluindo demanda, rotação, contenção e sobreposição.
O piloto formal continua pendente. Se uma correção técnica alterar algoritmos,
a necessidade de repetir a calibração deverá ser avaliada e registrada.

Os CSVs/soluções/logs brutos permanecem salvos localmente e ignorados pelo Git.
São versionados o plano e os relatórios técnicos, sem promover esta passagem
a conjunto de resultados científicos.

## Conclusão da passagem

Concluídas 918/918 execuções válidas, sem falhas de processo ou rejeições na
auditoria. Foram confirmadas 153 instâncias, seis métodos e zero interseção com
o piloto; 228 execuções A, 60 BENG e 630 CLASS. A auditoria integral foi repetida
após a retomada, conferindo recibos, hashes, CSVs e posicionamentos novamente.

A retomada reconheceu 918 execuções válidas, pulou todas e não executou métodos
novamente. Os hashes dos 918 recibos permaneceram idênticos; a comprovação está
em results/preflight/retomada.json e o log completo em retomada.log. O relatório
integridade.json contém o contrato, ambiente e contagens, sem métricas comparativas
de qualidade. A configuração e o selo da Tarefa 21 permanecem inalterados.

Não houve correção dos algoritmos ou dos parâmetros nesta etapa, portanto não
há necessidade identificada de refazer a calibração por causa desta passagem.
A próxima etapa é a Tarefa 22, piloto formal no Ryzen 3 já autorizado pelo usuário.
Esta passagem não selecionou H* e não integra a análise científica final.
