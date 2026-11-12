#ifndef ESTADO_REPARO_H
#define ESTADO_REPARO_H

#include "orientacao_externa.h"

using namespace std;

struct ChapaReparo {
    vector<int64_t> pecas;
    ResultadoDecodificacao resultado;
    ResultadoEmpacotaBase empacotamento;
};

struct EstadoReparo {
    vector<ChapaReparo> chapas;
};

struct Inviabilidade {
    int64_t excesso_area = 0;
    int64_t area_rejeitada = 0;
    int64_t chapas_inviaveis = 0;
    int64_t pecas_rejeitadas = 0;
};

Inviabilidade calcula_inviabilidade(const EstadoReparo& estado);
bool menor_inviabilidade(Inviabilidade candidata, Inviabilidade atual);
bool melhora_estado(const EstadoReparo& candidato, const EstadoReparo& atual);
EstadoReparo cria_estado_reparo(const Instancia& instancia, const Solucao& solucao);
void reempacota_chapa(const Instancia& instancia, EstadoReparo& estado, size_t indice, mt19937& gerador, CronometroCpu* relogio = nullptr, MecanismosBusca* mecanismos = nullptr);
EstadoReparo remove_e_redistribui(const Instancia& instancia, const Solucao& solucao, mt19937& gerador, CronometroCpu* relogio = nullptr, MecanismosBusca* mecanismos = nullptr);
Solucao solucao_do_reparo(const Instancia& instancia, const EstadoReparo& estado);

#endif
