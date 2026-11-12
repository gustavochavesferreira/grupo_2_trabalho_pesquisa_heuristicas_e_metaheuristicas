# Piloto final — configuração v2

Na raiz: `python3 scripts/piloto.py --max-minutos 420`.

São dez instâncias-piloto, quatro propostas e dez sementes comuns (1001–1010):
400 execuções válidas, com teto de 60 segundos de CPU cada. Configuração:
config/congelada_v2.cfg, duas chapas perturbadas, 1 milhão de avaliações de
reparo e 50000 reinícios por tentativa de redução. Operadores e fluxo do TP3
permanecem iguais. Paradas por LBref e encerramento do reparo continuam possíveis.

--max-minutos limita o tempo de parede da chamada inteira, incluindo preparação
e auditoria. No exemplo são sete horas; o teto nominal das execuções é 6h40 de
CPU, mais operações auxiliares. Não há garantia de conclusão em sete horas em
máquina compartilhada. Para reservar duas horas, use 120. O limite total não
altera os 60 segundos científicos por execução.

Ao atingir o teto total, SIGINT interrompe o grupo do orquestrador e do executável.
Resultados completos permanecem preservados; encerramento/limpeza pode levar
alguns segundos. Retorna 124, sem selecionar H* de matriz incompleta. Repita o
mesmo comando para retomar: o prazo recomeça e as execuções válidas são puladas
após auditoria. Ctrl+C também preserva os completos e retorna 130; erros retornam 1.
A barra avança por execução concluída ou conferida na retomada.

Saídas:

- results/pilot/congelada_v2/execucoes/: CSV, solução, recibo e logs;
- results/pilot/congelada_v2/: contrato, configuração e ambiente;
- results/pilot/resumo.csv e integridade.json: resumo e matriz validada;
- config/h_estrela_v2.json: escolha congelada somente após 400 validações.

H* usa menor desvio médio exato, maior alcance de LBref e menor mediana de tempo
até melhor K. Empate nos três preserva a ordem Hbase/Hext/Hint/Hcomb e registra
todas as empatadas, sem alegar superioridade exclusiva.

Somente planejar: `python3 scripts/piloto.py --planejar`.
Somente auditar dados existentes: `python3 scripts/piloto.py --analisar`.
Mantenha o terminal aberto, o computador ligado à tomada e sem suspensão.
Não altere código, configuração ou ambiente durante o lote e não rode em paralelo.

O selo v2 registra a escolha de parâmetros após exploração que incluiu instâncias
finais. O novo piloto não elimina essa exposição, que deve ser relatada no TE.
O histórico retirado da área ativa está em /tmp/tp3_historico.KEnHuf. Esse local
é temporário; copie para armazenamento permanente se quiser conservar o backup.
