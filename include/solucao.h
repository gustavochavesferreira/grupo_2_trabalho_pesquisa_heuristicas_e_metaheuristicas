#ifndef SOLUCAO_H
#define SOLUCAO_H

#include "instancia.h"

using namespace std;

struct Posicionamento {
    int64_t copia_id;
    size_t indice_chapa;
    int64_t x;
    int64_t y;
    int64_t largura;
    int64_t altura;
    bool rotacionada;
};

struct Chapa {
    vector<Posicionamento> posicionamentos;
};

struct Solucao {
    vector<Chapa> chapas;
};

struct ResultadoVerificacao {
    bool valido;
    string erro;
};

ResultadoVerificacao verifica_solucao(const Instancia& instancia, const Solucao& solucao);
void salva_solucao_csv(const Instancia& instancia, const Solucao& solucao, string caminho);

#endif
