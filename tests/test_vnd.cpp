#include "vnd.h"

#include <algorithm>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>

using namespace std;

void exige(bool ok, string erro) {
    if (!ok) throw runtime_error(erro);
}

Instancia linha(vector<int64_t> larguras) {
    Instancia i;
    i.largura = 10; i.altura = 1; i.area_chapa = 10;
    for (int64_t w : larguras) {
        int64_t id = static_cast<int64_t>(i.copias.size()) + 1;
        i.copias.push_back({id, i.tipos.size()});
        i.tipos.push_back({id, w, 1, 1, 0, 0});
        i.area_total += w;
    }
    return i;
}

EstadoReparo prepara(const Instancia& i, vector<vector<int64_t>> composicoes) {
    EstadoReparo e;
    mt19937 g(1001);
    for (auto pecas : composicoes) {
        ChapaReparo c; c.pecas = pecas;
        e.chapas.push_back(c);
        reempacota_chapa(i, e, e.chapas.size() - 1, g);
    }
    return e;
}

string retrato(const EstadoReparo& estado) {
    ostringstream s;
    for (const ChapaReparo& c : estado.chapas) {
        s << '[';
        for (int64_t id : c.pecas) s << id << ',';
        s << c.empacotamento.area_total << ':' << c.empacotamento.excesso_area << ':' << c.empacotamento.indice_melhor << ':' << c.empacotamento.tentativas.size();
        for (int64_t id : c.resultado.sequencia) s << ':' << id;
        for (int64_t id : c.resultado.rejeitadas) s << 'r' << id;
        for (auto p : c.resultado.chapa.posicionamentos) s << 'p' << p.copia_id << ',' << p.indice_chapa << ',' << p.x << ',' << p.y << ',' << p.largura << ',' << p.altura << ',' << p.rotacionada;
        s << ']';
    }
    return s.str();
}

void conserva_e_valida(const Instancia& i, const EstadoReparo& e) {
    set<int64_t> atribuicoes, colocadas;
    Solucao completa;
    for (size_t c = 0; c < e.chapas.size(); c++) {
        for (int64_t id : e.chapas[c].pecas) exige(atribuicoes.insert(id).second, "Movimento duplicou cópia.");
        Chapa chapa;
        for (auto p : e.chapas[c].resultado.chapa.posicionamentos) {
            exige(p.indice_chapa == c && colocadas.insert(p.copia_id).second, "Índice errado ou posição duplicada.");
            exige(find(e.chapas[c].pecas.begin(), e.chapas[c].pecas.end(), p.copia_id) != e.chapas[c].pecas.end(), "Peça posicionada na composição errada.");
            p.indice_chapa = completa.chapas.size(); chapa.posicionamentos.push_back(p);
        }
        if (!chapa.posicionamentos.empty()) completa.chapas.push_back(chapa);
    }
    exige(atribuicoes.size() == i.copias.size(), "Movimento perdeu cópia.");
    for (auto copia : i.copias) {
        exige(atribuicoes.count(copia.id), "ID original ausente.");
        if (!colocadas.count(copia.id)) {
            auto t = i.tipos[copia.indice_tipo];
            completa.chapas.push_back(Chapa{{{copia.id, completa.chapas.size(), 0, 0, t.largura, t.altura, false}}});
        }
    }
    exige(verifica_solucao(i, completa).valido, "Verificador independente rejeitou geometria.");
}

int main() {
    mt19937 g(1001);
    for (int viz = 1; viz <= 3; viz++) {
        auto i = viz == 1 ? linha({8, 4, 7}) : (viz == 2 ? linha({6, 5, 5, 3}) : linha({4, 4, 3, 2}));
        auto e = viz == 1 ? prepara(i, {{1, 2}, {3}}) : (viz == 2 ? prepara(i, {{1, 2}, {3, 4}}) : prepara(i, {{1, 2, 3}, {4}}));
        auto antes = retrato(e);
        auto r = explora_vizinhanca(i, e, viz, g);
        exige(r.melhorou && melhora_estado(r.estado, e), "Vizinhança não produziu a melhoria conhecida.");
        exige(r.avaliados == r.bases.size() && r.avaliados == 2, "Não avaliou toda a amostra.");
        exige(retrato(e) == antes, "Exploração alterou a origem.");
        if (viz == 1) exige(r.escolhido.base == 2, "Não escolheu a melhor realocação.");
        conserva_e_valida(i, r.estado);
    }
    auto i = linha({6, 5, 5, 3, 9});
    auto e = prepara(i, {{1, 2}, {3, 4}, {5}});
    auto movimento = cria_movimento(i, e, 0, 1, 2, g);
    exige(movimento.receptora == 1 && movimento.parceiro == 3, "Receptora ou parceiro de troca incorretos.");
    auto antes_terceira = retrato(EstadoReparo{{e.chapas[2]}});
    auto depois = aplica_movimento(i, e, movimento, g);
    exige(antes_terceira == retrato(EstadoReparo{{depois.chapas[2]}}), "Reempacotou chapa inalterada.");
    conserva_e_valida(i, depois);
    // A origem usa excesso antes de rejeição e preserva o menor índice em empate.
    EstadoReparo selecao; selecao.chapas.resize(3);
    selecao.chapas[0].resultado.area_rejeitada = 99;
    selecao.chapas[1].empacotamento.excesso_area = 1;
    selecao.chapas[2].empacotamento.excesso_area = 1;
    exige(escolhe_origem(selecao) == 1, "Prioridade de excesso ou empate de índice incorreto.");
    selecao.chapas[1].empacotamento.excesso_area = 0; selecao.chapas[2].empacotamento.excesso_area = 0;
    exige(escolhe_origem(selecao) == 0, "Origem por rejeição incorreta.");
    auto amostra_estado = prepara(linha({1,1,1,1,1,1,1,1,1,1}), {{1,2,3,4,5,6,7,8,9,10}});
    set<int64_t> vistas;
    for (int k = 0; k < 100; k++) {
        auto bases = amostra_bases_uniforme(amostra_estado, 0, 10, g);
        exige(bases.size() == 4 && set<int64_t>(bases.begin(), bases.end()).size() == 4, "Limite ceil(sqrt(T)) ou amostragem sem reposição incorretos.");
        vistas.insert(bases.begin(), bases.end());
    }
    exige(vistas.size() == 10, "Amostragem excluiu peças da origem.");
    // Caso em que a troca melhora e permite uma nova realocação: testa o retorno à primeira vizinhança.
    auto reinicio_i = linha({4, 7, 6, 6, 1, 6, 2});
    auto reinicio_e = prepara(reinicio_i, {{2,6}, {1,4,7}, {3,5}});
    mt19937 teste(1001);
    auto p1 = explora_vizinhanca(reinicio_i, reinicio_e, 1, teste);
    auto p2 = explora_vizinhanca(reinicio_i, reinicio_e, 2, teste);
    auto p3 = explora_vizinhanca(reinicio_i, p2.estado, 1, teste);
    exige(!p1.melhorou && p2.melhorou && p3.melhorou, "Caso de reinício perdeu as melhorias esperadas.");
    mt19937 g1(1001), g2(1001);
    auto v1 = executa_vnd(reinicio_i, reinicio_e, g1);
    auto v2 = executa_vnd(reinicio_i, reinicio_e, g2);
    exige(v1.melhorias[0] > 0 && v1.melhorias[1] > 0 && v1.reinicios >= 2, "VND não reiniciou após melhorar.");
    exige(retrato(v1.estado) == retrato(v2.estado) && g1 == g2 && v1.avaliacoes == v2.avaliacoes, "VND não reproduzível.");
    exige(calcula_inviabilidade(v1.estado).excesso_area == 2, "VND não atingiu a menor sobrecarga deste exemplo.");
    conserva_e_valida(reinicio_i, v1.estado);
    auto vazia_i = linha({2,3});
    auto vazia = prepara(vazia_i, {{}, {1,2}, {}});
    auto compacta = solucao_do_reparo(vazia_i, vazia);
    exige(compacta.chapas.size() == 1 && verifica_solucao(vazia_i, compacta).valido, "Não compactou chapas vazias na solução.");
    auto sem_busca = g;
    auto pronto = executa_vnd(vazia_i, vazia, g);
    exige(g == sem_busca && pronto.reinicios == 0, "VND buscou em estado já factível.");
    for (auto m : {MovimentoExterno{1,0,0,1,-1}, MovimentoExterno{3,0,1,1,1}, MovimentoExterno{2,0,1,99,3}}) {
        bool recusou = false;
        try { aplica_movimento(i, e, m, g); } catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "Movimento inválido aceito.");
    }
    mt19937 dados(1002);
    for (int caso = 0; caso < 60; caso++) {
        vector<int64_t> larguras;
        for (int n = 0; n < 8; n++) larguras.push_back(1 + dados() % 7);
        auto inst = linha(larguras);
        vector<vector<int64_t>> composicoes(3);
        for (int64_t id = 1; id <= 8; id++) composicoes[dados() % 3].push_back(id);
        auto inicial = prepara(inst, composicoes);
        auto fim = executa_vnd(inst, inicial, g);
        exige(!melhora_estado(inicial, fim.estado), "VND piorou o estado.");
        conserva_e_valida(inst, fim.estado);
        if (calcula_inviabilidade(fim.estado).chapas_inviaveis == 0) exige(verifica_solucao(inst, solucao_do_reparo(inst, fim.estado)).valido, "Aceitou solução inválida.");
    }
    cout << "VND: três melhorias conhecidas, amostragem, seleção, reinício, conservação e 60 estados aleatórios: OK\n";
}
