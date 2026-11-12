# Limites inferiores de referência

Fonte consultada: Dell'Amico, M.; Martello, S.; Vigo, D. **A lower bound for the
non-oriented two-dimensional bin packing problem**. Discrete Applied Mathematics,
118(1–2):13–24, 2002. PDF original em
`materiais_uteis_para_consulta/papers_citados_tp3/`.

## Implementação

O módulo pressupõe uma instância válida, como a produzida por `le_instancia`.
Retorna separadamente o limite por área, o limite DMV e `LBref`, o maior dos dois.

O limite por área é `ceil(area_total / (W*H))`. A divisão inteira evita perda de
precisão e não usa a soma `area_total + W*H - 1`, que poderia estourar.

Para DMV, a chapa é normalizada com `W >= H` e cada tipo com `w >= h`, sem mudar
a instância original. CUTSQ (p. 15) corta `floor(w/h)` quadrados de lado `h`,
gira o residual e repete enquanto `h > 1`. Multiplicidades incluem as demandas;
quadrados de lado 1 são descartados, como na fonte. Lados iguais ficam agrupados,
evitando materializar uma quantidade pseudo-polinomial de quadrados.

Para cada limiar inteiro `0 <= q <= floor(H/2)`, as equações (2)–(5) definem:

- S1: lado maior que `W-q`;
- S2: lado até `W-q` e maior que `W/2`;
- S3: lado até `W/2` e maior que `H/2`;
- S4: lado até `H/2` e pelo menos `q`.

As metades são comparadas por divisão inteira, preservando desigualdades estritas
também quando as dimensões são ímpares.

O Lema 2 emparelha os maiores quadrados de S3 que couberem ao lado dos de S2,
visitando os espaços residuais em ordem decrescente. Para os restantes de S3,
calcula-se:

```text
Ltil = |S2| + max(ceil(soma_lados_restantes / W),
                  ceil(quantidade_restante / floor(W / (floor(H/2)+1))))
```

S23 contém os elementos de S2 ou S3 com lado maior que `H-q`. A equação (7) é
calculada na forma algébrica equivalente:

```text
A = soma das áreas dos quadrados de S2, S3 e S4
D = soma de lado*(H-lado) para os quadrados de S23
L(q) = |S1| + max(Ltil, ceil((A+D)/(W*H)))
```

Essa forma evita multiplicar `W*H` por `Ltil`. Como os elementos de S23 têm lado
maior que `H/2`, cada parcela de D é menor que a área do quadrado. Portanto A+D
cabe em `uint64_t` quando a área original cabe em `int64_t`, mesmo que a soma
exceda o limite do inteiro com sinal.

O máximo de L(q) é a equação (8). Pelo Corolário 4, basta avaliar zero e os lados
distintos até `floor(H/2)`. O código recalcula os conjuntos para cada limiar,
com custo quadrático no número de lados distintos; não implementa a atualização
incremental descrita na análise de complexidade do artigo.

## Cuidados e validação

Este é o limite da equação (8), após CUTSQ, combinado com a área original em
`LBref`. O reforço opcional por um limite orientado L4, discutido mais adiante no
artigo, não faz parte desta implementação. Limites orientados não devem ser
aplicados diretamente às peças originais, pois aqui a rotação é permitida.

DMV isolado pode ser menor que o limite por área, pois CUTSQ descarta quadrados
unitários. `LBref` recupera essa informação. O desvio é
`100*(K-LBref)/LBref`; a função rejeita LBref não positivo ou K menor que LBref.

O exemplo publicado na p. 17, com chapa 23x20 e quadrados de lados
18 (duas cópias), 12 (duas), 11 (cinco) e 7 (seis), produz área 1835,
limite por área 4 e DMV 6. Há também regressão da decomposição 70x60 da Figura 1,
casos de fronteira, demandas, rotação e aritmética extrema. Com semente 1001,
300 casos são comparados com uma implementação literal que enumera todos os q;
outros 60 são confrontados com ótimos exatos por máscaras de células.
