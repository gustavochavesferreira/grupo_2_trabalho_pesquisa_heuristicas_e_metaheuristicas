#include "hbase.h"
#include "construcao_inicial.h"

#include <algorithm>
#include <iostream>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>

using namespace std;

void exige(bool ok, string erro) { if (!ok) throw runtime_error(erro); }

Instancia linha(vector<int64_t> larguras) {
    Instancia i; i.largura = 10; i.altura = 1; i.area_chapa = 10;
    for (int64_t w : larguras) {
        int64_t id = static_cast<int64_t>(i.copias.size()) + 1;
        i.copias.push_back({id, i.tipos.size()});
        i.tipos.push_back({id, w, 1, 1, 0, 0}); i.area_total += w;
    }
    return i;
}

EstadoReparo prepara(const Instancia& i, vector<vector<int64_t>> composicoes) {
    EstadoReparo e; mt19937 g(1001);
    for (auto pecas : composicoes) {
        ChapaReparo c; c.pecas = pecas; e.chapas.push_back(c);
        reempacota_chapa(i, e, e.chapas.size() - 1, g);
    }
    return e;
}

string retrato(const EstadoReparo& e) {
    ostringstream s;
    for (const auto& c : e.chapas) {
        s << '[';
        for (int64_t id : c.pecas) s << id << ',';
        for (auto p : c.resultado.chapa.posicionamentos) s << ':' << p.copia_id << ',' << p.x << ',' << p.y << ',' << p.rotacionada;
        s << ']';
    }
    return s.str();
}

string retrato_solucao(const Solucao& solucao) {
    ostringstream s;
    for (const auto& chapa : solucao.chapas) {
        s << '[';
        for (auto p : chapa.posicionamentos) s << p.copia_id << ',' << p.x << ',' << p.y << ',' << p.rotacionada << ';';
        s << ']';
    }
    return s.str();
}

int main() {
    auto melhora = linha({4,4,3,3,3,3});
    exige(constroi_solucao_inicial(melhora).chapas.size() == 3, "Exemplo deveria iniciar em três chapas.");
    auto r = executa_hbase(melhora, 1001, 10);
    exige(r.solucao.chapas.size() == 2 && r.reducoes_aceitas == 1 && r.tentativas_reducao == 1, "Hbase não reparou a redução conhecida.");
    exige(r.motivo_parada == "limite_inferior" && r.limites.referencia == 2, "Não parou em LBref.");
    exige(r.tempo_melhor >= 0 && r.tempo_melhor <= r.tempo_total, "Tempos inconsistentes.");
    exige(verifica_solucao(melhora, r.solucao).valido, "Solução de Hbase inválida.");
    auto repetida = executa_hbase(melhora, 1001, 10);
    exige(retrato_solucao(r.solucao) == retrato_solucao(repetida.solucao) && r.avaliacoes == repetida.avaliacoes, "Hbase não reproduzível sem parada temporal.");
    auto limite = executa_hbase(linha({6,6}), 1001, 10);
    exige(limite.motivo_parada == "limite_inferior" && limite.tentativas_reducao == 0, "Tentou reduzir solução já no limite.");
    ConfigHbase config; config.max_reinicios = 2;
    auto impossivel = linha({6,6,6});
    r = executa_hbase(impossivel, 1001, 10, config);
    exige(r.solucao.chapas.size() == 3 && r.reducoes_aceitas == 0 && r.perturbacoes == 2 && r.motivo_parada == "orcamento_reparo", "Orçamento de reinícios não respeitado.");
    exige(verifica_solucao(impossivel, r.solucao).valido, "Falha de reparo substituiu incumbente factível.");
    config.max_avaliacoes_reparo = 0;
    r = executa_hbase(melhora, 1001, 10, config);
    exige(r.tentativas_reducao == 0 && r.solucao.chapas.size() == 3, "Orçamento zero deveria preservar construção inicial.");
    config.max_avaliacoes_reparo = 1;
    r = executa_hbase(impossivel, 1001, 10, config);
    exige(r.avaliacoes == 0 && r.perturbacoes == 0, "Iniciou amostra que não cabia no orçamento.");
    auto e = prepara(impossivel, {{1,2}, {3}});
    mt19937 g(1001), antes = g;
    OrcamentoVnd pequeno{1,0};
    auto passo = explora_vizinhanca(impossivel, e, 1, g, nullptr, &pequeno);
    exige(passo.interrompida && passo.bases.empty() && g == antes, "Interrompeu orçamento depois de amostrar.");
    auto perturbacao_i = linha({4,3,2,1,5,2});
    auto original = prepara(perturbacao_i, {{1,2},{3,4},{5,6}});
    auto original_antes = retrato(original);
    mt19937 a(1002), b(1002);
    auto pa = perturba_estado(perturbacao_i, original, 2, a);
    auto pb = perturba_estado(perturbacao_i, original, 2, b);
    exige(retrato(pa) == retrato(pb) && a == b && retrato(original) == original_antes, "Perturbação alterou origem ou não é reproduzível.");
    set<int64_t> ids;
    size_t inalteradas = 0;
    for (size_t c = 0; c < pa.chapas.size(); c++) {
        if (retrato(EstadoReparo{{pa.chapas[c]}}) == retrato(EstadoReparo{{original.chapas[c]}})) inalteradas++;
        for (int64_t id : pa.chapas[c].pecas) exige(ids.insert(id).second, "Perturbação duplicou peça.");
    }
    exige(ids.size() == 6 && pa.chapas.size() == 3 && inalteradas >= 1, "Perturbação perdeu peças ou alterou chapa não selecionada.");
    CronometroCpu zero(0);
    bool parou = false;
    try { perturba_estado(perturbacao_i, original, 2, g, &zero); }
    catch (const TempoEsgotado&) { parou = true; }
    exige(parou && retrato(original) == original_antes, "Perturbação ignorou limite de CPU.");
    parou = false;
    Chapa vazia;
    try { insere_inferior_esquerdo(melhora, melhora.copias[0], vazia, 0, &zero); }
    catch (const TempoEsgotado&) { parou = true; }
    exige(parou && vazia.posicionamentos.empty(), "Inserção ignorou prazo ou deixou estado parcial.");
    parou = false;
    try { executa_hbase(melhora, 1001, 0); }
    catch (const TempoEsgotado&) { parou = true; }
    exige(parou, "Sem tempo para construção, não deve devolver uma solução parcial.");
    config.max_reinicios = 1000000; config.max_avaliacoes_reparo = 1000000;
    r = executa_hbase(impossivel, 1001, 0.03, config);
    exige(r.motivo_parada == "limite_cpu" && r.tempo_total >= 0.03 && verifica_solucao(impossivel, r.solucao).valido, "Parada real por CPU incorreta.");
    for (double invalido : {-1.0, numeric_limits<double>::infinity(), numeric_limits<double>::quiet_NaN()}) {
        bool recusou = false;
        try { executa_hbase(melhora, 1001, invalido); } catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "Limite inválido aceito.");
    }
    config.chapas_perturbadas = 1;
    bool recusou = false;
    try { executa_hbase(melhora, 1001, 10, config); } catch (const invalid_argument&) { recusou = true; }
    exige(recusou, "Configuração inválida aceita.");
    for (string nome : {"valida.txt", "area_64bits.txt", "espacos_crlf.txt"}) {
        auto instancia = le_instancia("tests/data/" + nome);
        auto final = executa_hbase(instancia, 1001, 10);
        exige(verifica_solucao(instancia, final.solucao).valido, "Hbase falhou nos casos bidimensionais e com rotação.");
    }
    cout << "Hbase: redução, LBref, VNS, conservação, reprodução, orçamento e CPU: OK\n";
}
