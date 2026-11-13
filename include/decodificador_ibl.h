#ifndef DECODIFICADOR_IBL_H
#define DECODIFICADOR_IBL_H

#include "solucao.h"
#include "tempo_cpu.h"

#include <unordered_map>

using namespace std;

struct ResultadoIBL {
    Solucao solucao;
    int64_t area_perfil = 0;
    // Área da chapa vezes K pode ultrapassar 64 bits, mesmo com área demandada válida.
    __uint128_t f7 = 0;
};

Posicionamento posiciona_ibl(Posicionamento p, const Chapa& chapa, int64_t largura, int64_t altura, CronometroCpu* relogio = nullptr);
int64_t area_perfil_superior(const Chapa& chapa, int64_t largura, int64_t altura, CronometroCpu* relogio = nullptr);
__uint128_t calcula_f7(int64_t area_chapa, size_t chapas, int64_t area_perfil);
// Decodificação completa e validada (referência; usada fora do laço da RLS).
ResultadoIBL decodifica_ibl(const Instancia& instancia, const vector<int64_t>& permutacao, CronometroCpu* relogio = nullptr);

// Decodificador incremental para o laço da RLS. Produz exatamente a mesma solução de
// decodifica_ibl, mas:
//  - reaproveita as chapas de uma decodificação anterior (`base`) cuja permutação é
//    idêntica à atual nas posições [0, inicio): o IBL só usa a última chapa aberta,
//    então o estado ao chegar em `inicio` é o mesmo;
//  - interrompe quando o número de chapas passa de `max_chapas`: nesse caso o f7 é
//    estritamente maior que o de qualquer solução com até max_chapas chapas;
//  - não revalida a solução a cada avaliação (a RLS valida a solução final).
class DecodificadorIbl {
    public:
        explicit DecodificadorIbl(const Instancia& instancia);
        // Retorna false se a decodificação foi interrompida por exceder max_chapas.
        bool decodifica(const vector<int64_t>& permutacao, const ResultadoIBL* base, size_t inicio,
                        size_t max_chapas, ResultadoIBL& saida, CronometroCpu* relogio = nullptr) const;
    private:
        const Instancia& instancia;
        unordered_map<int64_t, size_t> indices;
        vector<size_t> denso;
        vector<vector<int64_t>> copias;
        size_t tipo_de(int64_t valor) const;
};

#endif
