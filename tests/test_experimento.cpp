#include "experimento.h"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

using namespace std;

void exige(bool ok, string erro) { if (!ok) throw runtime_error(erro); }

int main() {
    vector<string> args{"--instancia","tests/data/valida.txt","--metodo","Hbase","--config","config/provisoria.cfg","--semente","4294967295","--cpu","0.5","--saida","/tmp/saida"};
    auto o = le_opcoes(args);
    exige(o.semente == 4294967295 && o.limite_cpu == 0.5 && !o.salvar_solucao && !o.ajuda, "Leitura das opções incorreta.");
    exige(le_opcoes({}).ajuda && le_opcoes({"--help"}).ajuda && le_opcoes({"--ajuda"}).ajuda, "Ajuda indisponível.");
    args.push_back("--salvar-solucao");
    exige(le_opcoes(args).salvar_solucao, "Não leu a opção de salvar solução.");
    for (string invalido : {"-1","+1","1.2","4294967296","18446744073709551616","1x",""}) {
        auto teste = args; teste[7] = invalido;
        bool recusou = false;
        try { le_opcoes(teste); } catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "Semente inválida aceita: " + invalido);
    }
    for (string invalido : {"0","-1","nan","inf","1,5","1x","1e9999","0x10","1 "}) {
        auto teste = args; teste[9] = invalido;
        bool recusou = false;
        try { le_opcoes(teste); } catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "CPU inválida aceita: " + invalido);
    }
    for (vector<string> invalido : vector<vector<string>>{{"--instancia"},{"--cpu","1"},{"--inexistente","1"},{"--help","--cpu","1"}}) {
        bool recusou = false;
        try { le_opcoes(invalido); } catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "Argumentos incompletos/desconhecidos aceitos.");
    }
    auto repetido = args; repetido.push_back("--salvar-solucao");
    bool recusou = false;
    try { le_opcoes(repetido); } catch (const invalid_argument&) { recusou = true; }
    exige(recusou, "Aceitou opção repetida.");
    auto marcos = calcula_evolucao({{0.2,5},{1.0,4},{9.0,3}}, 2);
    exige(!marcos[0].disponivel && marcos[1].chapas == 4 && marcos[2].chapas == 4 && marcos[3].chapas == 3 && marcos[5].desvio == 50, "Evolução comum usa eventos futuros ou perde redução.");
    char modelo[] = "/tmp/tp3_experimento_XXXXXX";
    char* temporario = mkdtemp(modelo);
    exige(temporario != nullptr, "Falha ao criar diretório de testes.");
    auto config = le_configuracao("config/provisoria.cfg");
    auto i = le_instancia("tests/data/valida.txt");
    o = le_opcoes(args); o.saida = string(temporario) + "/resultado"; o.limite_cpu = 10;
    auto r = executa_metodo(i, o, config);
    exige(r.busca.evolucao.size() == 6 && verifica_solucao(i, solucao_execucao(r)).valido, "Resultado comum inválido.");
    auto ruim = r; ruim.busca.solucao.chapas[0].posicionamentos.pop_back();
    recusou = false;
    try { registra_execucao(i, o, config, ruim); } catch (const runtime_error&) { recusou = true; }
    exige(recusou && !filesystem::exists(o.saida), "Registro inválido criou saída.");
    ruim = r; ruim.busca.evolucao[0].tempo = 0.2;
    recusou = false;
    try { registra_execucao(i, o, config, ruim); } catch (const invalid_argument&) { recusou = true; }
    exige(recusou && !filesystem::exists(o.saida), "Aceitou marcos inconsistentes.");
    string caminho = registra_execucao(i, o, config, r);
    exige(filesystem::is_regular_file(caminho), "Não gravou CSV validado.");
    ifstream arquivo(caminho); string antes((istreambuf_iterator<char>(arquivo)), istreambuf_iterator<char>());
    recusou = false;
    try { registra_execucao(i, o, config, r); } catch (const runtime_error&) { recusou = true; }
    ifstream novamente(caminho); string depois((istreambuf_iterator<char>(novamente)), istreambuf_iterator<char>());
    exige(recusou && antes == depois, "Sobrescreveu um resultado existente.");
    o.metodo = "RLS-f7"; o.saida = string(temporario) + "/rls"; config.rls.max_avaliacoes = 3;
    r = executa_metodo(i, o, config); r.rls.f7++;
    recusou = false;
    try { registra_execucao(i, o, config, r); } catch (const invalid_argument&) { recusou = true; }
    exige(recusou && !filesystem::exists(o.saida), "Aceitou f7 inconsistente.");
    filesystem::remove_all(temporario);
    cout << "Execução: argumentos, configuração, evolução comum, validação antes da escrita e proteção de saída: OK\n";
}
