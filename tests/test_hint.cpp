#include "hbase.h"

#include <iostream>
#include <stdexcept>

using namespace std;
void exige(bool ok, string erro) { if (!ok) throw runtime_error(erro); }

Instancia exemplo() {
    Instancia i; i.largura = 8; i.altura = 7; i.area_chapa = 56;
    vector<pair<int64_t,int64_t>> dimensoes{{2,2},{4,2},{2,4},{5,1},{5,1},{2,4},{1,1},{4,4}};
    for (auto d : dimensoes) {
        int64_t id = static_cast<int64_t>(i.tipos.size()) + 1;
        i.copias.push_back({id,i.tipos.size()}); i.tipos.push_back({id,d.first,d.second,1,0,0}); i.area_total += d.first*d.second;
    }
    return i;
}

int main() {
    auto i = exemplo(); mt19937 g(1001);
    auto base = empacota_base(i, {1,2,3,4,5,6,7,8}, g);
    auto inicial = base.tentativas[base.indice_melhor];
    MetricasInternas metricas; vector<MovimentoInterno> registro;
    auto resultado = busca_interna(i, inicial, 0, metricas, nullptr, &registro);
    exige(inicial.area_rejeitada == 5 && resultado.area_rejeitada == 4 && metricas.melhorias > 0, "Hint não melhorou o caso conhecido.");
    exige(metricas.ativacoes == 1 && metricas.decodificacoes == registro.size() && registro.size() <= 16, "Métricas ou orçamento incorretos.");
    // Reproduz cada avaliação pela trilha efetivamente executada e confere primeira melhoria.
    auto atual = inicial;
    size_t proxima_distancia = 1; bool fase_troca = false;
    for (auto movimento : registro) {
        exige(movimento.origem == static_cast<size_t>(atual.posicao_primeira_rejeitada), "Não retomou a primeira rejeição após melhorar.");
        exige(movimento.troca == fase_troca && movimento.destino == movimento.origem - proxima_distancia, "Ordem de inserções/trocas incorreta.");
        auto candidata = decodifica_inferior_esquerdo(i, altera_sequencia(atual.sequencia, movimento));
        if (melhora_empacotamento(candidata, atual)) {
            atual = candidata; proxima_distancia = 1; fase_troca = false;
        } else {
            proxima_distancia++;
            if (proxima_distancia > 8 || proxima_distancia > movimento.origem) { proxima_distancia = 1; fase_troca = true; }
        }
    }
    exige(atual.sequencia == resultado.sequencia, "Não aceitou a primeira melhoria encontrada.");
    Instancia sem_melhoria; sem_melhoria.largura = 10; sem_melhoria.altura = 10; sem_melhoria.area_chapa = 100; sem_melhoria.area_total = 90;
    sem_melhoria.tipos = {{1,3,3,10,0,0}};
    vector<int64_t> ids;
    for (int64_t id = 1; id <= 10; id++) { sem_melhoria.copias.push_back({id,0}); ids.push_back(id); }
    auto incompleta = decodifica_inferior_esquerdo(sem_melhoria, ids);
    MetricasInternas limite; registro.clear();
    auto fim = busca_interna(sem_melhoria, incompleta, 0, limite, nullptr, &registro);
    exige(limite.decodificacoes == 16 && registro.size() == 16 && fim.area_rejeitada == 9, "Não respeitou as 16 decodificações.");
    for (size_t n = 0; n < 16; n++) exige(registro[n].troca == (n >= 8) && registro[n].destino == 8 - n % 8, "Não examinou oito anteriores na ordem correta.");
    MetricasInternas completa;
    auto ok = decodifica_inferior_esquerdo(i, {1});
    busca_interna(i, ok, 0, completa);
    exige(completa.ativacoes == 0 && completa.decodificacoes == 0, "Ativou em empacotamento completo.");
    MecanismosBusca m; m.orientacao_interna = true;
    EstadoReparo estado; estado.chapas.resize(1); estado.chapas[0].pecas = {1,2,3,4,5,6,7,8};
    mt19937 mesmo(1001); reempacota_chapa(i, estado, 0, mesmo, nullptr, &m);
    exige(estado.chapas[0].empacotamento.tentativas.size() == 8 && estado.chapas[0].resultado.area_rejeitada == 4 && m.metricas_internas.ativacoes == 1, "Busca interna não integrada após as oito tentativas.");
    exige(m.historico.dados.empty(), "Hint criou histórico externo.");
    auto fecha = exemplo();
    vector<pair<int64_t,int64_t>> dimensoes{{3,1},{2,2},{4,2},{4,3},{3,3},{2,2},{2,5},{2,3}};
    fecha.area_total = 0;
    for (size_t t = 0; t < dimensoes.size(); t++) {
        fecha.tipos[t].largura = dimensoes[t].first; fecha.tipos[t].altura = dimensoes[t].second;
        fecha.area_total += dimensoes[t].first * dimensoes[t].second;
    }
    MecanismosBusca completo; completo.orientacao_interna = true;
    EstadoReparo concluido; concluido.chapas.resize(1); concluido.chapas[0].pecas = {1,2,3,4,5,6,7,8};
    mt19937 semente(1001); reempacota_chapa(fecha, concluido, 0, semente, nullptr, &completo);
    exige(completo.metricas_internas.completos == 1 && completo.metricas_internas.decodificacoes == 11, "Não registrou empacotamento completo conhecido.");
    exige(verifica_solucao(fecha, solucao_do_reparo(fecha, concluido)).valido, "Conclusão interna não foi validada.");
    // Completa as rejeitadas em chapas individuais para conferir geometria e conservação.
    Solucao solucao{{estado.chapas[0].resultado.chapa}};
    for (int64_t id : estado.chapas[0].resultado.rejeitadas) {
        auto t = i.tipos[i.copias[id-1].indice_tipo];
        solucao.chapas.push_back(Chapa{{{id,solucao.chapas.size(),0,0,t.largura,t.altura,false}}});
    }
    exige(verifica_solucao(i, solucao).valido, "Busca interna perdeu peças ou criou posições inválidas.");
    auto final = executa_hint(i, 1001, 10);
    exige(final.metodo == "Hint" && verifica_solucao(i, final.solucao).valido && final.orientacao_externa.atualizacoes == 0, "Hint inválida ou orientada externamente.");
    cout << "Hint: primeira rejeição, inserções/trocas, reinício, 16 avaliações, métricas e integração: OK\n";
}
