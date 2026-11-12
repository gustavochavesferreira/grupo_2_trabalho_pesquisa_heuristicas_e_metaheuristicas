#include "apresentacao.h"
#include "experimento.h"

#include <iostream>

using namespace std;

int main(int argc, char* argv[]) {
    try {
        vector<string> argumentos;
        for (int i = 1; i < argc; i++) argumentos.push_back(argv[i]);
        auto opcoes = le_opcoes(argumentos);
        if (opcoes.ajuda) {
            apresenta_projeto(cout);
            apresenta_uso(cout);
            return 0;
        }
        auto config = le_configuracao(opcoes.configuracao);
        confere_destino(opcoes, config);
        auto instancia = le_instancia(opcoes.instancia);
        auto resultado = executa_metodo(instancia, opcoes, config);
        string caminho = registra_execucao(instancia, opcoes, config, resultado);
        cout << "Resultado validado: " << caminho << '\n';
        return 0;
    } catch (const TempoEsgotado&) {
        cerr << "Erro: limite de CPU atingido antes da primeira solução completa; nenhum resultado foi registrado.\n";
        return 3;
    } catch (const exception& erro) {
        cerr << "Erro: " << erro.what() << "\nUse --ajuda para consultar a interface.\n";
        return 1;
    }
}
