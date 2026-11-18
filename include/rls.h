#ifndef RLS_H
#define RLS_H

#include "decodificador_ibl.h"
#include "limites_inferiores.h"
#include "evolucao.h"
#include <random>
#include <utility>

using namespace std;

struct ConfigRls {
    uint64_t max_avaliacoes = 100000000;
    // Variante diagnóstica (não é a RLS-f7 publicada): parte da construção gulosa.
    // A gulosa vira a incumbente e a busca parte de uma permutação induzida por ela.
    bool inicial_gulosa = false;
    // Ordens/orientações tentadas por chapa para o IBL reproduzi-la numa chapa só.
    uint64_t tentativas_por_chapa = 1000;
};

struct MovimentoRls {
    size_t primeira = 0;
    size_t segunda = 0;
    bool troca = false;
    uint64_t sorteios_parceiro = 0;
};

using MarcoRls = MarcoEvolucao;

struct ResultadoRls {
    string metodo = "RLS-f7";
    Solucao solucao;
    vector<int64_t> permutacao;
    LimitesInferiores limites{};
    __uint128_t f7 = 0;
    int64_t area_perfil = 0;
    uint64_t avaliacoes = 0;
    uint64_t trocas = 0;
    uint64_t inversoes = 0;
    uint64_t aceitos = 0;
    uint64_t melhorias = 0;
    double tempo_total = 0;
    double tempo_melhor = 0;
    string motivo_parada;
    vector<MarcoRls> evolucao;
};

vector<int64_t> permutacao_inicial_rls(const Instancia& instancia, mt19937& gerador, CronometroCpu* relogio = nullptr);
// Permutação assinada induzida por uma solução: chapa a chapa, procura (ordens fixas, depois
// sorteadas) uma ordem/orientação das peças da chapa que o IBL empacote numa chapa só; sem
// sucesso, usa a ordem (y, x). Cada tentativa é uma decodificação contada em `avaliacoes`,
// que não passa de `limite`.
vector<int64_t> permutacao_da_solucao(const Instancia& instancia, const Solucao& solucao, mt19937& gerador,
                                      uint64_t tentativas_por_chapa, uint64_t limite, uint64_t& avaliacoes,
                                      CronometroCpu* relogio = nullptr);
MovimentoRls sorteia_movimento_rls(const vector<int64_t>& permutacao, mt19937& gerador, CronometroCpu* relogio = nullptr);
void aplica_movimento_rls(vector<int64_t>& permutacao, MovimentoRls movimento);
bool aceita_rls(__uint128_t candidata, __uint128_t atual);
vector<MarcoRls> evolucao_rls(const vector<pair<double, int64_t>>& melhorias, int64_t limite_referencia);
ResultadoRls executa_rls(const Instancia& instancia, uint32_t semente, double limite_cpu, ConfigRls config = {});

#endif
