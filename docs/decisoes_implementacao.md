# Decisões de implementação — registro ativo

- A pedido de ampliar o piloto preliminar para cerca de uma hora, adicionados
  A23 e CLASS 3/60/02 em bloco separado de 24 execuções (results/ta_v1_extra/),
  sem modificar o contrato original de 36. O mesmo comando completa os dois e
  publica resumo_ampliado.csv com as 60 execuções, exigindo mesmo ambiente.
  O teto de parede padrão passou a 75 minutos; CPU permanece 60 s por execução.

- Para a entrega preliminar V1, o usuário pediu três sementes e menos instâncias.
  Criado piloto_v1.py com A14 e CLASS 7/60/02 e 9/60/02, quatro métodos e três
  sementes: 36 execuções com até 60 s de CPU e 45 min de parede por chamada.
  Não escolhe H* oficial. O parcial formal foi movido sob trava livre para
  /tmp/tp3_piloto_parcial.qedoXN, preservando recuperação. Ver docs/piloto_v1.md.

- Por solicitação do usuário, fixados 1 milhão de candidatos e 50000 reinícios
  por tentativa de redução, duas chapas perturbadas e 60 segundos de CPU.
  A escolha sucede exploração que incluiu instâncias finais; não se reivindica
  independência dessa exploração em relação ao benchmark.
- O C++ não foi alterado. Instâncias, sementes, métodos, operadores, aceitação
  e limites internos do TP3 permanecem iguais.
- Configuração e sementes têm selo SHA-256 v2. H* será selecionada novamente
  no piloto completo, com selo próprio; nenhuma escolha prévia é reutilizada.
- --max-minutos limita tempo de parede da chamada, sem reduzir o orçamento
  científico por execução. SIGINT ao grupo encerra orquestrador e filho atual;
  completos são retomáveis e matriz incompleta não produz H*. Teto retorna
  124; Ctrl+C retorna 130.
- Artefatos obsoletos de parâmetros e execuções relacionadas foram retirados
  do projeto e preservados em /tmp/tp3_historico.KEnHuf, inclusive o registro
  histórico das decisões. A limpeza não apaga a proveniência. O diretório
  temporário não constitui backup permanente.
- Geometria inteira, cópias com vínculo ao tipo, validação independente, relógio
  de CPU e retomada por contrato/recibo continuam vigentes. Documentação ativa:
  docs/execucao.md, docs/experimentos.md e docs/piloto.md.
