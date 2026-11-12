#ifndef EXPERIMENTO_H
#define EXPERIMENTO_H

#include "hbase.h"
#include "rls.h"
#include <ostream>

using namespace std;

struct OpcoesExecucao {
    bool ajuda = false;
    string instancia;
    string metodo;
    string configuracao;
    uint32_t semente = 0;
    double limite_cpu = 0;
    string saida;
    bool salvar_solucao = false;
};

struct ConfigExperimento {
    string id;
    string estado;
    ConfigHbase busca;
    ConfigRls rls;
};

struct ResultadoExecucao {
    string metodo;
    ResultadoHbase busca{};
    ResultadoRls rls{};
};

void apresenta_uso(ostream& saida);
OpcoesExecucao le_opcoes(const vector<string>& argumentos);
ConfigExperimento le_configuracao(string caminho);
ResultadoExecucao executa_metodo(const Instancia& instancia, const OpcoesExecucao& opcoes, const ConfigExperimento& config);
const Solucao& solucao_execucao(const ResultadoExecucao& resultado);
void confere_destino(const OpcoesExecucao& opcoes, const ConfigExperimento& config);
string registra_execucao(const Instancia& instancia, const OpcoesExecucao& opcoes, const ConfigExperimento& config, const ResultadoExecucao& resultado);

#endif
