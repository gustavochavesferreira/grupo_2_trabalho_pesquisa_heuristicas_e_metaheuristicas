#include "experimento.h"

#include <algorithm>
#include <iostream>
#include <sstream>
#include <stdexcept>

using namespace std;

void exige(bool ok, string erro) { if (!ok) throw runtime_error(erro); }

string retrato(const ResultadoExecucao& r) {
    ostringstream texto;
    texto << r.metodo << '|';
    for (const auto& chapa : solucao_execucao(r).chapas) {
        texto << '[';
        for (auto p : chapa.posicionamentos) texto << p.copia_id << ',' << p.indice_chapa << ',' << p.x << ',' << p.y << ',' << p.largura << ',' << p.altura << ',' << p.rotacionada << ';';
        texto << ']';
    }
    if (r.metodo == "RLS-f7") {
        texto << '|' << r.rls.avaliacoes << ',' << r.rls.trocas << ',' << r.rls.inversoes << ',' << r.rls.aceitos << ',' << r.rls.melhorias;
        for (auto v : r.rls.permutacao) texto << ',' << v;
    } else {
        auto e = r.busca.orientacao_externa; auto i = r.busca.orientacao_interna;
        texto << '|' << r.busca.avaliacoes << ',' << r.busca.tentativas_reducao << ',' << r.busca.reducoes_aceitas << ',' << r.busca.perturbacoes
              << ',' << e.atualizacoes << ',' << e.reinicios << ',' << e.movimentos_orientados << ',' << e.melhorias_aceitas
              << ',' << i.ativacoes << ',' << i.decodificacoes << ',' << i.melhorias << ',' << i.completos;
    }
    return texto.str();
}

int main() {
    vector<string> metodos{"Hbase","Hext","Hint","Hcomb","Haleat","RLS-f7"};
    vector<string> caminhos{"tests/data/integracao/limite_inicial.txt", "tests/data/integracao/reducao.txt", "tests/data/integracao/orcamento.txt", "tests/data/integracao/interna.txt", "tests/data/valida.txt", "tests/data/area_64bits.txt"};
    auto config = le_configuracao("config/provisoria.cfg");
    config.busca.max_reinicios = 1; config.busca.max_avaliacoes_reparo = 40; config.rls.max_avaliacoes = 80;
    OpcoesExecucao o; o.limite_cpu = 2;
    size_t execucoes = 0;
    bool houve_reducao = false;
    for (string caminho : caminhos) {
        auto i = le_instancia(caminho);
        auto copias = i.copias;
        for (string metodo : metodos) {
            o.metodo = metodo;
            for (uint32_t semente : {1001,1002}) {
                o.semente = semente;
                auto a = executa_metodo(i, o, config), b = executa_metodo(i, o, config);
                execucoes += 2;
                exige(verifica_solucao(i, solucao_execucao(a)).valido && verifica_solucao(i, solucao_execucao(b)).valido, "Integração perdeu factibilidade em " + metodo);
                exige(retrato(a) == retrato(b), "Reprodução divergente: " + metodo + " em " + caminho);
                const auto& evolucao = metodo == "RLS-f7" ? a.rls.evolucao : a.busca.evolucao;
                auto limites = metodo == "RLS-f7" ? a.rls.limites : a.busca.limites;
                auto parada = metodo == "RLS-f7" ? a.rls.motivo_parada : a.busca.motivo_parada;
                double total = metodo == "RLS-f7" ? a.rls.tempo_total : a.busca.tempo_total;
                double melhor = metodo == "RLS-f7" ? a.rls.tempo_melhor : a.busca.tempo_melhor;
                exige(melhor >= 0 && melhor <= total && evolucao.size() == 6, "Tempos ou marcos ausentes.");
                int64_t k = static_cast<int64_t>(solucao_execucao(a).chapas.size());
                exige(k >= limites.referencia && (parada == "limite_inferior") == (k == limites.referencia), "Parada não corresponde a LBref.");
                int64_t anterior = static_cast<int64_t>(i.copias.size());
                for (auto marco : evolucao) if (marco.disponivel) {
                    exige(marco.chapas >= k && marco.chapas <= anterior && marco.desvio == desvio_percentual(marco.chapas, limites.referencia), "Evolução inconsistente.");
                    anterior = marco.chapas;
                }
                if (metodo == "RLS-f7") {
                    auto decodificado = decodifica_ibl(i, a.rls.permutacao);
                    exige(decodificado.f7 == a.rls.f7 && a.rls.avaliacoes <= 80 && a.rls.avaliacoes >= 1, "f7 ou teto da RLS inconsistente.");
                } else {
                    exige(a.busca.controle_auxiliar == (metodo == "Haleat"), "Haleat não identificada como controle auxiliar.");
                    exige(a.busca.avaliacoes <= 40*a.busca.tentativas_reducao, "Excedeu orçamento de reparo.");
                    if (metodo != "Hext" && metodo != "Hcomb") exige(a.busca.orientacao_externa.atualizacoes == 0 && a.busca.orientacao_externa.movimentos_orientados == 0, "Histórico vazou entre métodos.");
                    if (metodo == "Hbase" || metodo == "Hext") exige(a.busca.orientacao_interna.ativacoes == 0, "Busca interna ativada no método errado.");
                    houve_reducao |= a.busca.reducoes_aceitas > 0;
                }
                if (caminho.ends_with("limite_inicial.txt")) exige(k == 1 && parada == "limite_inferior" && (metodo == "RLS-f7" ? a.rls.avaliacoes == 1 : a.busca.tentativas_reducao == 0), "Tentou buscar após alcance inicial do limite.");
                if (caminho.ends_with("orcamento.txt")) exige(k == 3 && parada == (metodo == "RLS-f7" ? "limite_avaliacoes" : "orcamento_reparo"), "Falha de reparo/limite de avaliações não preservou incumbente.");
            }
        }
        exige(i.copias.size() == copias.size(), "Busca alterou a instância.");
        for (size_t c = 0; c < copias.size(); c++) exige(i.copias[c].id == copias[c].id && i.copias[c].indice_tipo == copias[c].indice_tipo, "Busca alterou cópias/tipos de origem.");
    }
    exige(houve_reducao, "Matriz não exercitou redução aceita.");
    auto impossivel = le_instancia("tests/data/integracao/orcamento.txt");
    config.busca.max_reinicios = 1000000; config.busca.max_avaliacoes_reparo = 1000000; config.rls.max_avaliacoes = 100000000;
    o.limite_cpu = 0.03; o.semente = 1001;
    for (string metodo : metodos) {
        o.metodo = metodo;
        auto r = executa_metodo(impossivel, o, config);
        auto parada = metodo == "RLS-f7" ? r.rls.motivo_parada : r.busca.motivo_parada;
        double tempo = metodo == "RLS-f7" ? r.rls.tempo_total : r.busca.tempo_total;
        exige(parada == "limite_cpu" && tempo >= o.limite_cpu && verifica_solucao(impossivel, solucao_execucao(r)).valido, "Parada real por CPU inválida: " + metodo);
    }
    cout << "Integração: " << execucoes << " execuções em seis instâncias/seis métodos, duas sementes, reprodução, conservação e seis paradas reais por CPU: OK\n";
}
