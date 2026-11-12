# TP3 — Heurísticas para o Corte de Estoque Bidimensional

Projeto de Heurísticas e Metaheurísticas da UFMG. O objetivo é minimizar o número
de chapas retangulares idênticas necessárias para atender exatamente às demandas
de tipos de peças retangulares. O empacotamento é ortogonal e livre, permite
rotação de 90 graus e exige contenção e ausência de sobreposição. Cortes têm
espessura nula e sobras não têm valor.

## Estado atual

**Tarefa 1 concluída: estrutura inicial.** O programa apenas apresenta o projeto.
Leitura de instâncias, heurísticas, verificador de soluções e experimentos serão
implementados nas tarefas correspondentes. Nenhum resultado experimental é
produzido neste estágio.

Os seis nomes de métodos previstos para execução são:

| Nome | Papel no estudo |
| --- | --- |
| `Hbase` | Configuração proposta de referência, com seleção uniforme e empacotador-base. |
| `Hext` | Configuração proposta com orientação externa pelo histórico de rejeições. |
| `Hint` | Configuração proposta com orientação interna pela primeira rejeição. |
| `Hcomb` | Configuração proposta que reúne orientação externa e interna. |
| `Haleat` | Controle auxiliar de `Hint`, com escolhas aleatórias na busca interna. |
| `RLS-f7` | Comparadora independente da literatura, de Zhao et al. (2024). |

`Haleat` é apenas um controle auxiliar, não uma heurística proposta adicional.
Esses nomes ainda não acionam algoritmos no executável inicial `bin/tp3`.

## Dependências, compilação e testes

Use Linux, GNU Make e GCC com suporte a C++20 (`g++`). Não há bibliotecas externas
necessárias para este estado inicial. Na raiz do projeto:

```bash
make
./bin/tp3
make test
make clean
```

`make` compila com `-std=c++20 -O2 -Wall -Wextra -Wpedantic`.
`make test` compila e executa o teste C++ da apresentação e executa o programa.
`make clean` remove somente os executáveis, objetos e dependências gerados pelo
Makefile. Os cabeçalhos são acompanhados por dependências automáticas.

## Organização

```text
include/                       Cabeçalhos C++
src/                           Código C++
tests/                         Testes C++ simples
scripts/                       Reservado aos scripts de preparação e experimentação
config/                        Reservado às configurações
instances/source/              Instâncias brutas fornecidas manualmente (ignoradas)
results/                       Resultados gerados (ignorados por padrão)
docs/decisoes_implementacao.md  Registro cumulativo de decisões
Makefile                       Compilação, testes e limpeza
bin/ e obj/                    Artefatos de compilação (ignorados)
```

Os diretórios existentes `codigo_exemplo/`, `enunciado/`, `papers_citados_tp3/`,
`materiais_uteis_consulta/` e `guia_experimentos_heuristicas/` são materiais de
referência. O código TSP em `codigo_exemplo/` é referência de estilo e organização;
ele não faz parte da solução nem da compilação deste projeto.

## Instâncias e reprodução

Forneça manualmente as famílias A, BENG e CLASS em `instances/source/`, seguindo
as [instruções locais](instances/source/README.md). Não renomeie os originais.
Dados brutos ficam fora do Git; manifestos, instruções e metadados serão
versionados quando a seleção for implementada.

O protocolo previsto exige sementes explícitas, execução oficial sequencial em
uma thread, limite de CPU incluindo construção e busca e validação independente
das soluções. Calibração, piloto e congelamento dos parâmetros devem preceder
o benchmark final. Esses mecanismos ainda não estão implementados.

## Fontes acadêmicas e precedência

1. **Ferreira, G. C.; Carvalhido, L. J.; Gomide, F. L.** Desenvolvimento de
   heurísticas para o Problema de Corte de Estoque Bidimensional. Projeto TP3,
   UFMG, 2026. Arquivo local: `TP3 - Grupo 2 - Heurísticas e Metaheurísticas.pdf`.
   É a especificação principal do problema, dos métodos e dos experimentos.
2. **Zhao, R.; Liang, T.; Wu, Z.; van den Berg, D.; Thürer, M.; Weise, T.**
   Randomized Local Search on the 2D Rectangular Bin Packing Problem with Item
   Rotation. GECCO '24 Companion, p. 235–238, 2024.
   [DOI: 10.1145/3638530.3654139](https://doi.org/10.1145/3638530.3654139).
   PDF local em `papers_citados_tp3/`. Fonte da comparadora RLS-f7.
3. **Heurísticas e Metaheurísticas — Roteiros dos trabalhos avaliativos
   (TP/TE/TA)**. UFMG. Arquivo local:
   `enunciado/HeM - Roteiro dos trabalhos de pesquisa.pdf`.
4. **Dell'Amico, M.; Martello, S.; Vigo, D.** A lower bound for the non-oriented
   two-dimensional bin packing problem. Discrete Applied Mathematics,
   118(1–2):13–24, 2002. PDF local em `papers_citados_tp3/`. Fonte prevista
   para o limite inferior com rotação.
5. **Iori, M.; de Lima, V. L.; Martello, S.; Monaci, M.** 2DPackLib: A
   two-dimensional cutting and packing library. Optimization Letters,
   16:471–480, 2022. PDF local em `papers_citados_tp3/`.

Em conflitos, prevalece o TP3. Nesta tarefa foram consultados o TP3, o artigo da
RLS, o roteiro da disciplina e o código de exemplo; nenhuma implementação
externa da RLS foi consultada ou copiada. Decisões futuras não fixadas pelas
fontes devem ser justificadas em `docs/decisoes_implementacao.md`.

## Primeiro repositório e commit manual

Todas as operações Git e GitHub são responsabilidade do usuário. No GitHub, crie
um repositório vazio, sem README, licença ou `.gitignore` gerados pelo serviço.
Na raiz local, inicialize a branch `main` se ainda não houver repositório:

```bash
git init -b main
git status
git diff --check
git diff
git add .gitignore README.md Makefile include/apresentacao.h src/apresentacao.cpp src/main.cpp tests/test_inicio.cpp docs/decisoes_implementacao.md scripts/.gitkeep config/.gitkeep instances/source/README.md results/README.md
git diff --cached --check
git diff --cached
git commit -m "chore: cria estrutura inicial do projeto"
```

`git diff` não mostra arquivos novos ainda não adicionados; revise-os também pelo
editor e confira o diff preparado antes do commit. A lista explícita de caminhos
evita incluir dados ou materiais de consulta por acidente.

Depois do commit, substitua `SEU_USUARIO` e `SEU_REPOSITORIO` abaixo e cadastre o
remoto, caso ainda não esteja configurado:

```bash
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

Se já houver repositório ou remoto configurado, preserve a configuração existente
e pule a inicialização ou o cadastro correspondente. Nenhum desses comandos é
executado automaticamente pelo projeto.
