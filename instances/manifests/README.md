# Catálogo e seleção do TP3

Gerados por `make catalog`, com Python 3 (biblioteca padrão) e o leitor C++ da
Tarefa 2. Os dados originais devem ser fornecidos manualmente em `instances/source/`.

- `catalogo.csv`: 553 instâncias fornecidas: 43 A, dez BENG e 500 CLASS.
- `piloto.csv`: dez instâncias: cinco A e cinco CLASS.
- `final.csv`: 153 instâncias: 38 A, dez BENG e 105 CLASS.

O campo `caminho` é relativo a `instances/source/`, inclusive as subpastas da
extração original. `identificador` é o nome original sem a extensão `.ins2D`.
Classe, tamanho e réplica ficam vazios para A e BENG. `sha256` identifica os
bytes originais, permitindo conferir os dados após baixá-los novamente.

As A são ordenadas por total de cópias e identificador textual crescente. As
posições 1, 11, 22, 33 e 43 correspondem, respectivamente, a A42 (13 cópias),
A30 (39), A17 (135), A23 (248) e A14 (809). Elas integram o piloto com as CLASS
de tamanho 60, réplica 02 e classes 1, 3, 5, 7 e 9.

O conjunto final contém as A restantes, todas as BENG, as CLASS das réplicas 01
e 06 nas dez classes e cinco tamanhos, e as CLASS de tamanho 60, réplica 02,
classes 2, 4, 6, 8 e 10. Nenhuma instância-piloto integra o conjunto final.

O script valida todos os arquivos catalogados pelo leitor C++, exige as 163
instâncias necessárias ao piloto/final e rejeita nomes desconhecidos, IDs de
instância duplicados e conteúdo inválido. Outras CLASS válidas são catalogadas
sem integrar a seleção. Apenas `README.md` e `format_description.txt` são
ignorados na varredura. ZIPs devem ser extraídos fora da pasta ou removidos dela
manualmente após a extração.

Todos os dados são conferidos antes da gravação dos CSVs. A ordenação dos
registros é pelo caminho original; executar novamente com a mesma entrada
produz os mesmos arquivos. Para verificar reprodução e seleção: `make catalog-test`.
