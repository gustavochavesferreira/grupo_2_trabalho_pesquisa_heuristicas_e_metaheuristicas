# Soluções completas — CSV versão 1

`salva_solucao_csv(instancia, solucao, caminho)` valida a solução antes de abrir
o arquivo de saída. Em caso de solução inválida ou falha de gravação, lança
`std::runtime_error`. Um arquivo existente só é sobrescrito após a validação.

Cada linha representa uma cópia posicionada:

```csv
versao,copia_id,tipo_id,chapa,x,y,largura,altura,rotacionada
1,1,1,0,0,0,2,3,0
1,2,1,0,2,0,2,3,0
```

- `copia_id`: identificador único da expansão das demandas.
- `tipo_id`: ID original do tipo na instância.
- `chapa`: índice da chapa no vetor da solução, começando em zero.
- `x,y`: canto inferior esquerdo, em coordenadas inteiras.
- `largura,altura`: dimensões efetivamente usadas.
- `rotacionada`: 0 para a orientação original; 1 para rotação de 90 graus.

O CSV deve ser interpretado junto da instância correspondente. As linhas seguem
a ordem das chapas e dos posicionamentos. Não há chapas vazias em uma solução
aceita; o número de chapas é a quantidade de índices distintos.

`verifica_solucao` retorna validade e o primeiro erro encontrado. Ele consulta
a instância para conferir cópias, tipos e demandas e verifica a geometria
diretamente, sem depender de decisões ou rotinas dos empacotadores. Seu custo
inclui a comparação de todos os pares de peças de cada chapa.
