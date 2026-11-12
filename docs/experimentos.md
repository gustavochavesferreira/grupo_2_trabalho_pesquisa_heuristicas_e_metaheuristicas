# Lotes sequenciais e retomada

Requer Linux, Python 3.9+ (biblioteca padrão), GNU Make e GCC C++20. Na raiz:

```bash
python3 scripts/piloto.py --planejar
```

`--planejar` confere configuração, seleção, sementes e hashes das instâncias e
mostra a matriz, sem compilar ou executar métodos. Remover essa opção inicia o
lote. A configuração científica ativa é config/congelada_v2.cfg. Comando com
teto total de sete horas: `python3 scripts/piloto.py --max-minutos 420`.

| Modo | Instâncias | Métodos | Sementes/CPU |
|---|---|---|---|
| `calibration` | piloto; aceita subconjunto explícito | quatro propostas; aceita subconjunto | padrão 1001/1 segundo; aceita sementes comuns e CPU reduzida |
| `pilot` | dez do piloto | quatro propostas | dez sementes/60 segundos: 400 execuções |
| `preflight` | 153 finais, disjuntas do piloto | seis | uma semente comum/CPU curta, padrão 1001/1 segundo: 918 execuções |
| `final` | 153 finais; aceita subconjunto para separar famílias | seis | dez sementes/60 segundos: 9180 execuções no conjunto completo |

Os modos pilot/preflight/final exigem `estado=congelado` e teto da RLS de
100000000. O piloto verifica o selo v2 e seleciona H* somente após validar sua
matriz completa. O modo genérico calibration permanece para testes da
infraestrutura; nenhum estudo histórico depende dele no fluxo ativo.

Opções: `--config ARQUIVO` e `--modo` são obrigatórios; `--saida DIRETORIO`
padrão `results/`; `--source DIRETORIO` padrão `instances/source/` para os dados
fornecidos manualmente. `--instancias ID ...`, `--metodos NOME ...`,
`--sementes NUMERO ...` e `--cpu SEGUNDOS` só permitem as escolhas da tabela.
As dez sementes versionadas são exatamente 1001 a 1010. Não se alteram os
manifestos, nem se baixam instâncias. Os arquivos brutos precisam corresponder
aos hashes dos manifestos existentes. As instâncias são executadas na ordem do
manifesto, depois métodos e sementes na ordem das listas.

## Artefatos e identidade do lote

A saída fica em `<saida>/<modo>/<config_id>/`:

- `contrato.json`: plano, parâmetros, hashes dos manifestos, sementes, configuração,
  código, executável, scripts e identificação do ambiente.
- `config.cfg`: cópia exata da configuração usada pela CLI.
- `ambiente.json`: data UTC, compilador/versão, opções de compilação e ligação,
  kernel, sistema, modelo da CPU, RAM, Python e hashes do código/executável.
- `execucoes/<instancia>__<metodo>__<semente>/`: CSV, solução completa,
  stdout/stderr e `concluida.json` com comando, início/fim UTC e checksums.
- `.pendentes/`: tentativas ainda não publicadas, inclusive falhas/interrupções.
- `invalidos/`: versões anteriormente publicadas que falharam na conferência.

Antes do primeiro lote com uma combinação de código/compilador/flags, o script
força a compilação e guarda um carimbo em `bin/protocolo-build.json`. Nas próximas
chamadas, reutiliza o executável somente se assinatura e hash coincidirem. Isso
impede registrar flags diferentes das realmente usadas nos objetos. O código é
identificado por SHA-256 dos fontes/cabeçalhos/Makefile, sem comandos Git.

Cada lote tem contrato fixo. Para mudar CPU, sementes, lista de instâncias,
configuração, executável, scripts ou ambiente, use outro `--saida` (ou outro ID
para uma configuração nova). Isso evita misturar protocolos. O contrato não
congela uma grade nem escolhe parâmetros: apenas preserva a identidade do lote.

## Retomada e interrupção

Repita **o mesmo comando** para retomar. Cada resultado concluído é novamente
conferido: recibo, identidade, configuração, hashes, CSV, métricas, evolução e
geometria da solução exportada. Só então é pulado. Cabeçalhos completos da versão 1 são obrigatórios; um marco
posterior ao término deve conservar o K final. A geometria confere cópias,
demandas, tipo, orientação, contenção e sobreposição; perfil/f7 também são
recalculados. Essa conferência complementa o verificador independente C++ que
já valida cada solução no executável.

Uma execução nova roda em diretório temporário no mesmo filesystem. O retorno
precisa ser zero e os dois CSVs precisam passar pela validação. O recibo é
escrito por arquivo temporário e substituição atômica; depois uma renomeação do
diretório inteiro publica o conjunto. Assim, interromper entre CSV e solução não
cria uma execução concluída. Uma versão inválida é movida para `invalidos/`,
sem apagar outras execuções; depois é refeita. Pendências antigas ficam para
inspeção e não são consideradas resultados científicos.

`Ctrl+C` encerra e aguarda o filho atual, retornando 130. Erros retornam 1 e
preservam os logs; corrigida a causa, repita o comando. CPU insuficiente para
construir a inicial não fabrica resultado: o lote para e preserva a tentativa.
Se for necessário mudar o orçamento, use outro lote.

O orquestrador usa a trava global `results/.execucao.lock`, mesmo se a saída for
outro diretório. O filho herda a trava: se o pai morrer abruptamente, outro lote
não pode iniciar enquanto aquele filho continuar. Execuções e lotes são
sequenciais; não há paralelismo. Faça todas as execuções oficiais por esse
orquestrador; abrir manualmente outra CLI fora dele não participa da trava.
Não remova o arquivo da trava para liberar processos: o bloqueio é do kernel e
é liberado quando todos os descritores se fecham.

A medição de CPU continua sendo a da CLI: inclui construção, busca, limites,
validações internas e evolução, sem incluir compilação, leitura/saída em disco
ou a auditoria adicional do orquestrador. Não se usa tempo de parede como
substituto do limite científico de CPU.

## Verificação da infraestrutura

```bash
make orchestration-test
```

Os testes usam diretórios temporários e uma instância real pequena do piloto
(A42), com reparo desligado e orçamentos curtos. Conferem retomada sem repetição,
CSV truncado, geometria corrompida mesmo com checksum atualizado, preservação
dos outros resultados, pendências, alteração de protocolo, trava herdada,
interrupção e ausência de publicação quando a execução falha. Os planos de
400/918/9180 execuções são conferidos sem executá-los. Nenhum resultado desses
testes integra calibração, piloto ou benchmark.
