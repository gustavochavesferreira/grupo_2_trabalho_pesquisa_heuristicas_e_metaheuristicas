#ifndef HBASE_H
#define HBASE_H

#include "vnd.h"
#include "limites_inferiores.h"
#include "evolucao.h"

using namespace std;

struct ConfigHbase {
    size_t chapas_perturbadas = 2;
    size_t max_reinicios = 5;
    size_t max_avaliacoes_reparo = 1000;
};

struct ResultadoHbase {
    string metodo = "Hbase";
    bool controle_auxiliar = false;
    MetricasExternas orientacao_externa;
    MetricasInternas orientacao_interna;
    Solucao solucao;
    LimitesInferiores limites{};
    size_t tentativas_reducao = 0;
    size_t reducoes_aceitas = 0;
    size_t perturbacoes = 0;
    size_t avaliacoes = 0;
    double tempo_total = 0;
    double tempo_melhor = 0;
    string motivo_parada;
    vector<MarcoEvolucao> evolucao;
};

EstadoReparo perturba_estado(const Instancia& instancia, const EstadoReparo& estado, size_t quantidade_chapas, mt19937& gerador, CronometroCpu* relogio = nullptr, MecanismosBusca* mecanismos = nullptr);
ResultadoHbase executa_hbase(const Instancia& instancia, uint32_t semente, double limite_cpu, ConfigHbase config = {});

ResultadoHbase executa_hext(const Instancia& instancia, uint32_t semente, double limite_cpu, ConfigHbase config = {});

ResultadoHbase executa_hint(const Instancia& instancia, uint32_t semente, double limite_cpu, ConfigHbase config = {});

ResultadoHbase executa_haleat(const Instancia& instancia, uint32_t semente, double limite_cpu, ConfigHbase config = {});

ResultadoHbase executa_hcomb(const Instancia& instancia, uint32_t semente, double limite_cpu, ConfigHbase config = {});

#endif
