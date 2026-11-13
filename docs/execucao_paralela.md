# Execução paralela exploratória e monitor de RAM

Novo módulo independente; os executores sequenciais e seus resultados não foram
substituídos. Requer Linux com /proc, Python 3.9+, Make e GCC C++20, configuração
v2 e as mesmas instâncias de instances/source/. Não instala bibliotecas extras.

## Comandos

Benchmark reduzido (108 execuções, seis métodos, seis instâncias, três sementes):

```bash
python3 scripts/benchmark_paralelo.py
```

Usa automaticamente um trabalhador por núcleo físico disponível, até o número
de instâncias. Para deixar parte da CPU livre ou limitar o consumo de memória:

```bash
python3 scripts/benchmark_paralelo.py --trabalhadores 2
```

Matriz completa, mas em regime paralelo exploratório (9180 execuções):

```bash
python3 scripts/benchmark_paralelo.py --completo
```

Use --planejar para conferir sem executar; --analisar para revalidar uma matriz
completa e gerar a tabela. Opcional: --max-minutos N limita a fase de execução
dos trabalhadores por tempo de parede, sem alterar os 60 segundos de CPU de cada
execução. Compilação inicial e auditoria final ficam fora desse teto opcional.

Cada trabalhador recebe uma instância inteira e roda seus métodos/sementes em
sequência. Ao terminar, recebe a próxima instância. Cada processo C++ continua
com uma thread e herda afinidade a uma única CPU lógica de um núcleo físico.
Threads SMT do mesmo núcleo não são usadas como núcleos independentes. Se a
topologia do sistema não estiver disponível, a seleção usa as CPUs permitidas
pela afinidade do processo. Não se garante divisão linear do tempo pelo número
de núcleos: há instâncias mais demoradas e disputa por recursos compartilhados.

Ctrl+C solicita parada aos trabalhadores, encerra os executáveis em andamento
e preserva completos. Repita o mesmo comando, com os mesmos trabalhadores e
ambiente, para retomar. A trava global impede sobreposição com os executores
sequenciais: não remova seu arquivo para contornar o bloqueio. Um erro de
trabalhador interrompe o lote e mantém os logs e pendências para diagnóstico.

## RAM a cada minuto

O console exibe, no início, a cada 60 segundos e ao encerrar:

```text
[RAM 60s] atual 420.1 MiB | pico observado 485.6 MiB | disponível 3500 MiB | swap processos 0.0 MiB
```

O monitor amostra a cada segundo o RSS do controlador, trabalhadores e seus
descendentes (inclusive C++), e salva ram.csv com uso atual, pico observado da
sessão, pico do último intervalo, swap dos processos e RAM disponível/swap do
sistema inteiro. A cada retomada começa uma nova sessão; o CSV é acrescido, com
data UTC e tempo decorrido daquela sessão. Monitoramento inclui conferência nos
trabalhadores; não continua durante a auditoria final feita pelo controlador.

É **pico observado por amostragem**, não pico exato do kernel: alocações entre
amostras podem passar despercebidas. A soma de RSS pode contar páginas
compartilhadas mais de uma vez, especialmente após fork. RAM disponível é uma
métrica do computador inteiro, não apenas deste programa. Os valores ajudam
a detectar pressão de memória; não demonstram, sozinhos, um gargalo de RAM.
Queda persistente da memória disponível e crescimento de swap são sinais para
investigar e reduzir trabalhadores. Não é implementada limitação automática de
RAM nem alteração automática do número de trabalhadores durante o lote.

## Resultados e interpretação

Diretórios separados:

- results/paralelo/reduzido/congelada_v2/
- results/paralelo/completo/congelada_v2/

Contêm contrato.json (ambiente, CPUs, hashes e tarefas), ambiente.json,
config.cfg, execucoes/ com resultados/soluções/recibos/logs, .pendentes/,
ram.csv, integridade.json e tabela_comparacao.csv. Cada recibo novo registra a
CPU lógica usada. Uma instância permanece no mesmo núcleo durante sua passagem;
na retomada a distribuição entre os mesmos núcleos pode mudar. Configuração,
matriz, código ou CPUs diferentes exigem um lote separado, não mistura de dados.
Os resultados paralelos são ignorados pelo Git por padrão; faça backup da pasta.

Cada conjunto de arquivos é publicado após validação independente e renomeação
do diretório. Corrupção em resultado publicado provoca erro e é preservada para
inspeção. A tabela só aparece depois de conferir toda a matriz.

O TP3 prevê um processo cronometrado por vez. Portanto, mesmo --completo aqui é
exploratório: não substitui silenciosamente o benchmark oficial sequencial, não
seleciona H* e não exige H*. Concorrência muda cache, largura de banda de memória,
temperatura e frequência; o mesmo tempo de CPU pode produzir soluções diferentes.
Não misture os resultados com results/final/ ou com o benchmark reduzido
sequencial. Uma adoção oficial da paralelização precisaria ser autorizada.

## Verificação

```bash
python3 -B tests/test_paralelo.py
```

Testa leitura e agregação de RAM, registros periódicos, duas instâncias pequenas
com seis métodos em dois núcleos, recibos/afinidade, reauditoria sem repetição e
interrupção com encerramento do subprocesso. Esses dados são temporários e não
integram os experimentos científicos.
