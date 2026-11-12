# Instâncias originais

Coloque manualmente neste diretório os arquivos das famílias **A**, **BENG** e
**CLASS** fornecidos para o trabalho, no formato unificado da 2DPackLib.
Preserve os nomes e o conteúdo dos originais. Não use as instâncias TSP de
`codigo_exemplo/` como entrada deste projeto.

O formato previsto contém a quantidade de tipos, as dimensões `W H` da chapa e,
para cada tipo, os campos `id wi hi di bi pi`. O leitor C++ está disponível pela
função `le_instancia`, declarada em `include/instancia.h`.

Após extrair os conjuntos, execute `make catalog` na raiz. O comando requer
Python 3 e gera os CSVs em `instances/manifests/`. `make catalog-test` verifica
a seleção e as falhas esperadas usando cópias temporárias dos arquivos reais.
Subpastas criadas na extração dos ZIPs são aceitas; os nomes não são alterados.

Os dados brutos deste diretório, inclusive subdiretórios, são ignorados pelo Git.
Somente este arquivo de instruções deve ser versionado aqui. Não baixe ou crie
instâncias para substituir dados ausentes. Manifestos e metadados de reprodução
serão mantidos fora deste diretório.
