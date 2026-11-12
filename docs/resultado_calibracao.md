# Resultado da calibração da Tarefa 21

Executadas e revalidadas 160 execuções, exclusivamente nas dez instâncias-piloto,
com as quatro opções e quatro propostas do plano em calibracao.md. Semente 1001,
CPU máxima de três segundos; CPU efetiva acumulada de 100,482268078 segundos.
Não foram executados piloto formal, preflight ou benchmark final.

| Opção | Desvio médio (%) | K médio | Alcance de LBref | Mediana até melhor K (s) | CPU média (s) |
|---|---:|---:|---:|---:|---:|
| base | 9,071153 | 20,6 | 30% | 0,002360014 | 0,623328 |
| chapas3 | 9,071153 | 20,6 | 30% | 0,002362321 | 0,626071 |
| reinicios10 | 9,071153 | 20,6 | 30% | 0,002370637 | 0,638977 |
| reparo2000 | 9,071153 | 20,6 | 30% | 0,002389430 | 0,623681 |

Aplicando o critério pré-definido, venceu cal21_base pelo desempate de tempo
mediano até o melhor K. Qualidade e alcance empataram. As diferenças temporais
são muito pequenas, com uma única semente; não sustentam superioridade
estatística. A calibração não encontrou vantagem de qualidade nas alternativas
e conservou os valores provisórios, agora congelados para todos os métodos da
arquitetura: duas chapas perturbadas, cinco reinícios e 1000 candidatos por
reparo. O teto da RLS permanece 100000000; não foi calibrado.

A grade não estima interações entre fatores e três segundos podem limitar o
esforço antes de consumir os maiores orçamentos. Isso não permite concluir que
mais reinícios ou avaliações sejam inúteis em 60 segundos. Não se escolheu H*;
a escolha entre métodos cabe ao piloto formal da Tarefa 22.

## Artefatos e reprodução

- config/calibracao/: quatro opções avaliadas.
- results/calibration/cal21_*/: contratos, ambiente, 160 resultados e soluções,
  recibos com hashes e logs originais. Os dados brutos não foram reescritos.
- results/calibration/resumo.csv e por_metodo.csv: resumos da matriz completa.
- config/congelada_v1.cfg: configuração comum, somente leitura (0444).
- config/congelada_v1.json: selo com SHA-256, critério, plano e contratos.

```bash
python3 scripts/calibrar.py --executar
python3 scripts/calibrar.py --analisar
python3 scripts/verificar_congelamento.py
python3 tests/test_calibracao.py
```

A execução repetida do primeiro comando reconheceu as 160 execuções válidas e
pulou todas, sem refazê-las. A análise repetida preservou configuração e selo.
O teste de congelamento rejeita uma escolha diferente e alterações de conteúdo.
Antes das próximas etapas, execute verificar_congelamento.py; não edite a
configuração ou o selo. O contrato dos lotes também registra o hash da cópia
usada. Dados brutos incluem caminhos absolutos do ambiente original; em outra
máquina, preserve os originais e use outro diretório de saída para reprodução.

## Ambiente e limite de interpretação

Execuções no ambiente conectado: AMD Ryzen 3 5300U, GCC 13.3.0 (Ubuntu), Linux;
kernel, RAM e opções exatas estão nos arquivos ambiente.json. O TP3 descreve
Ryzen 5 5600/32 GB/Linux Mint 22 para os experimentos. Esta calibração local não
altera silenciosamente esse ambiente previsto: antes do piloto formal deve-se
resolver a execução no hardware previsto ou autorizar/documentar uma alteração
no protocolo. Em particular, desempates por tempo são específicos da máquina.
