#include "solucao.h"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <stdexcept>

using namespace std;

void exige(bool condicao, string motivo) {
    if (!condicao) throw runtime_error(motivo);
}

void rejeita(const Instancia& instancia, const Solucao& solucao, string motivo) {
    auto resultado = verifica_solucao(instancia, solucao);
    exige(!resultado.valido && resultado.erro.find(motivo) != string::npos, "Erro não detectado: " + motivo);
}

int main() {
    auto instancia = le_instancia("tests/data/espacos_crlf.txt");
    Solucao base{{Chapa{{{1, 0, 0, 0, 2, 3, false}, {2, 0, 2, 0, 2, 3, false}}}}};
    exige(verifica_solucao(instancia, base).valido, "Contato vertical deve ser permitido.");
    auto s = base;
    s.chapas[0].posicionamentos[1].x = 0;
    s.chapas[0].posicionamentos[1].y = 3;
    exige(verifica_solucao(instancia, s).valido, "Contato horizontal deve ser permitido.");
    s.chapas[0].posicionamentos[1].x = 2;
    exige(verifica_solucao(instancia, s).valido, "Contato pelo vértice deve ser permitido.");
    s.chapas[0].posicionamentos[1] = {2, 0, 7, 4, 3, 2, true};
    exige(verifica_solucao(instancia, s).valido, "Rotação e bordas superiores devem ser permitidas.");
    s = base;
    s.chapas.push_back(Chapa{{{2, 1, 0, 0, 2, 3, false}}});
    s.chapas[0].posicionamentos.pop_back();
    exige(verifica_solucao(instancia, s).valido, "Coordenadas iguais em chapas distintas são permitidas.");
    s.chapas[1].posicionamentos[0].copia_id = 1;
    rejeita(instancia, s, "duplicada");
    s = base;
    s.chapas[0].posicionamentos.pop_back();
    rejeita(instancia, s, "ausente");
    rejeita(instancia, Solucao{}, "ausente");
    s = base;
    s.chapas[0].posicionamentos[1].copia_id = 99;
    rejeita(instancia, s, "desconhecido");
    s.chapas[0].posicionamentos[1].copia_id = -1;
    rejeita(instancia, s, "desconhecido");
    s = base;
    s.chapas[0].posicionamentos[0].indice_chapa = 1;
    rejeita(instancia, s, "Índice");
    s = base;
    s.chapas[0].posicionamentos[0].rotacionada = true;
    rejeita(instancia, s, "orientação");
    for (auto dimensao : {0LL, -1LL, 4LL}) {
        s = base;
        s.chapas[0].posicionamentos[0].largura = dimensao;
        rejeita(instancia, s, "orientação");
    }
    for (auto coordenada : {-1LL, 10LL, numeric_limits<long long>::max()}) {
        s = base;
        s.chapas[0].posicionamentos[0].x = coordenada;
        rejeita(instancia, s, "fora");
        s = base;
        s.chapas[0].posicionamentos[0].y = coordenada;
        rejeita(instancia, s, "fora");
    }
    s = base;
    s.chapas[0].posicionamentos[1].x = 1;
    rejeita(instancia, s, "Sobreposição");
    s.chapas[0].posicionamentos[1].x = 0;
    rejeita(instancia, s, "Sobreposição");
    s = base;
    s.chapas.push_back({});
    rejeita(instancia, s, "vazia");
    auto alterada = instancia;
    alterada.tipos[0].demanda = 3;
    rejeita(alterada, base, "Demanda");
    alterada = instancia;
    alterada.copias[0].indice_tipo = 99;
    rejeita(alterada, base, "Instância");
    alterada = instancia;
    alterada.copias[1].id = 1;
    rejeita(alterada, base, "Instância");
    alterada = instancia;
    alterada.tipos[0].altura = 2;
    s = base;
    for (auto& p : s.chapas[0].posicionamentos) { p.altura = 2; p.rotacionada = true; }
    exige(verifica_solucao(alterada, s).valido, "Quadrados podem ser marcados como rotacionados.");
    auto grande = le_instancia("tests/data/area_64bits.txt");
    Solucao grande_sol{{Chapa{{{1, 0, 0, 0, 100000, 100000, false}}},
                       Chapa{{{2, 1, 0, 0, 100000, 100000, true}}}}};
    exige(verifica_solucao(grande, grande_sol).valido, "Falha com dimensões de área acima de 32 bits.");
    // Cada tipo em uma chapa própria isola a verificação de demandas repetidas e IDs de tipo fora de ordem.
    auto repetidas = le_instancia("tests/data/valida.txt");
    Solucao separada;
    for (CopiaPeca copia : repetidas.copias) {
        TipoPeca tipo = repetidas.tipos[copia.indice_tipo];
        bool gira = tipo.altura > repetidas.altura;
        separada.chapas.push_back(Chapa{{{copia.id, separada.chapas.size(), 0, 0,
            gira ? tipo.altura : tipo.largura, gira ? tipo.largura : tipo.altura, gira}}});
    }
    exige(verifica_solucao(repetidas, separada).valido, "Demandas repetidas ou rotação obrigatória rejeitadas.");

    auto nome = "tp3_solucao_" + to_string(chrono::steady_clock::now().time_since_epoch().count()) + ".csv";
    auto caminho = filesystem::temp_directory_path() / nome;
    salva_solucao_csv(instancia, base, caminho.string());
    ifstream arquivo(caminho);
    string csv((istreambuf_iterator<char>(arquivo)), istreambuf_iterator<char>());
    arquivo.close();
    exige(csv == "versao,copia_id,tipo_id,chapa,x,y,largura,altura,rotacionada\n1,1,1,0,0,0,2,3,0\n1,2,1,0,2,0,2,3,0\n", "CSV incompleto ou incorreto.");
    bool recusou = false;
    try { salva_solucao_csv(instancia, Solucao{}, caminho.string()); }
    catch (const runtime_error&) { recusou = true; }
    exige(recusou, "Exportação aceitou solução inválida.");
    ifstream preservado(caminho);
    string depois((istreambuf_iterator<char>(preservado)), istreambuf_iterator<char>());
    exige(csv == depois, "Exportação inválida alterou arquivo existente.");
    preservado.close();
    filesystem::remove(caminho);
    recusou = false;
    try { salva_solucao_csv(instancia, base, (caminho / "ausente.csv").string()); }
    catch (const runtime_error&) { recusou = true; }
    exige(recusou, "Falha de abertura não diagnosticada.");
    cout << "Testes do modelo, verificador independente e exportação CSV: OK\n";
}
