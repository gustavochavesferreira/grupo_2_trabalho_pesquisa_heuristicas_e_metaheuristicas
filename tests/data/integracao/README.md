# Instâncias pequenas dos testes integrados

Estes casos dirigidos são testes, fora dos manifestos científicos:

- `limite_inicial.txt`: uma chapa, LBref atingido na inicial.
- `reducao.txt`: construção em três chapas, com arranjo factível em duas.
- `orcamento.txt`: três peças 6x1 em chapa 10x1; LBref=2, mas são necessárias três.
- `interna.txt`: o caso 8x7 usado nos testes de orientação interna e combinação.

Os testes também reutilizam `../valida.txt` (demandas repetidas, rotação obrigatória,
IDs de tipo fora de ordem) e `../area_64bits.txt` (áreas acima de 32 bits).
Nada desse diretório integra catálogo, calibração, piloto ou benchmark.
