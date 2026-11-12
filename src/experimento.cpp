#include "experimento.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <locale>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>

using namespace std;

bool metodo_conhecido(string metodo) {
    return metodo == "Hbase" || metodo == "Hext" || metodo == "Hint" || metodo == "Hcomb" || metodo == "Haleat" || metodo == "RLS-f7";
}

uint64_t inteiro_opcao(string texto, uint64_t maximo, string nome) {
    if (texto.empty() || texto.find_first_not_of("0123456789") != string::npos) throw invalid_argument(nome + " deve ser um inteiro não negativo.");
    size_t fim = 0;
    uint64_t valor;
    try { valor = stoull(texto, &fim); }
    catch (const exception&) { throw invalid_argument(nome + " está fora da faixa permitida."); }
    if (fim != texto.size() || valor > maximo) throw invalid_argument(nome + " está fora da faixa permitida.");
    return valor;
}

double cpu_opcao(string texto) {
    if (!regex_match(texto, regex("[0-9]+(\\.[0-9]+)?([eE][+-]?[0-9]+)?"))) throw invalid_argument("--cpu deve ser um número positivo em segundos, com ponto decimal.");
    double valor;
    try { valor = stod(texto); }
    catch (const exception&) { throw invalid_argument("--cpu está fora da faixa permitida."); }
    if (!isfinite(valor) || valor <= 0) throw invalid_argument("--cpu deve ser finito e maior que zero.");
    return valor;
}

void apresenta_uso(ostream& saida) {
    saida << "Uso: ./bin/tp3 --instancia ARQUIVO --metodo METODO --config ARQUIVO\n"
          << "              --semente INTEIRO --cpu SEGUNDOS --saida DIRETORIO [--salvar-solucao]\n"
          << "Métodos: Hbase, Hext, Hint, Hcomb, Haleat (controle auxiliar), RLS-f7.\n"
          << "A semente deve estar entre 0 e 4294967295; CPU usa ponto decimal e deve ser positiva.\n"
          << "Configuração: arquivo chave=valor; exemplo em config/provisoria.cfg.\n"
          << "Gera um CSV por execução validada; recusa sobrescrever resultados ou soluções.\n"
          << "--salvar-solucao grava também os posicionamentos em CSV. --ajuda ou --help mostra esta ajuda.\n";
}

OpcoesExecucao le_opcoes(const vector<string>& argumentos) {
    OpcoesExecucao opcoes;
    if (argumentos.empty() || (argumentos.size() == 1 && (argumentos[0] == "--ajuda" || argumentos[0] == "--help"))) {
        opcoes.ajuda = true;
        return opcoes;
    }
    map<string, string> valores;
    set<string> conhecidas{"--instancia", "--metodo", "--config", "--semente", "--cpu", "--saida", "--salvar-solucao"};
    for (size_t i = 0; i < argumentos.size(); i++) {
        string opcao = argumentos[i];
        if (!conhecidas.count(opcao)) throw invalid_argument("Opção desconhecida: " + opcao);
        if (valores.count(opcao)) throw invalid_argument("Opção repetida: " + opcao);
        if (opcao == "--salvar-solucao") valores[opcao] = "1";
        else {
            if (i + 1 == argumentos.size() || argumentos[i + 1].starts_with("--") || argumentos[i + 1].empty()) throw invalid_argument("Falta valor para " + opcao);
            valores[opcao] = argumentos[++i];
        }
    }
    for (string obrigatoria : {"--instancia", "--metodo", "--config", "--semente", "--cpu", "--saida"}) {
        if (!valores.count(obrigatoria)) throw invalid_argument("Opção obrigatória ausente: " + obrigatoria);
    }
    opcoes.instancia = valores.at("--instancia");
    opcoes.metodo = valores.at("--metodo");
    if (!metodo_conhecido(opcoes.metodo)) throw invalid_argument("Método desconhecido: " + opcoes.metodo);
    opcoes.configuracao = valores.at("--config");
    opcoes.semente = static_cast<uint32_t>(inteiro_opcao(valores.at("--semente"), numeric_limits<uint32_t>::max(), "--semente"));
    opcoes.limite_cpu = cpu_opcao(valores.at("--cpu"));
    opcoes.saida = valores.at("--saida");
    opcoes.salvar_solucao = valores.count("--salvar-solucao") > 0;
    return opcoes;
}

string sem_espacos(string texto) {
    size_t inicio = texto.find_first_not_of(" \t\r\n");
    if (inicio == string::npos) return "";
    return texto.substr(inicio, texto.find_last_not_of(" \t\r\n") - inicio + 1);
}

ConfigExperimento le_configuracao(string caminho) {
    ifstream arquivo(caminho);
    if (!arquivo) throw runtime_error("Não foi possível abrir a configuração: " + caminho);
    set<string> conhecidas{"versao", "id", "estado", "chapas_perturbadas", "max_reinicios", "max_avaliacoes_reparo", "rls_max_avaliacoes"};
    map<string, string> valores;
    string linha;
    size_t numero = 0;
    while (getline(arquivo, linha)) {
        numero++;
        linha = sem_espacos(linha);
        if (linha.empty() || linha[0] == '#') continue;
        size_t igual = linha.find('=');
        if (igual == string::npos) throw invalid_argument("Configuração, linha " + to_string(numero) + ": esperado chave=valor.");
        string chave = sem_espacos(linha.substr(0, igual)), valor = sem_espacos(linha.substr(igual + 1));
        if (!conhecidas.count(chave) || valor.empty() || valores.count(chave)) throw invalid_argument("Configuração, linha " + to_string(numero) + ": chave desconhecida, repetida ou valor vazio: " + chave);
        valores[chave] = valor;
    }
    if (arquivo.bad()) throw runtime_error("Falha ao ler a configuração: " + caminho);
    for (string chave : conhecidas) if (!valores.count(chave)) throw invalid_argument("Configuração sem a chave obrigatória: " + chave);
    if (valores.at("versao") != "1") throw invalid_argument("Versão de configuração não suportada.");
    ConfigExperimento config;
    config.id = valores.at("id");
    config.estado = valores.at("estado");
    if (!regex_match(config.id, regex("[A-Za-z0-9][A-Za-z0-9_.-]*"))) throw invalid_argument("id da configuração deve usar letras ASCII, números, ponto, hífen ou sublinhado.");
    if (config.estado != "provisorio" && config.estado != "congelado") throw invalid_argument("estado da configuração deve ser provisorio ou congelado.");
    config.busca.chapas_perturbadas = inteiro_opcao(valores.at("chapas_perturbadas"), numeric_limits<size_t>::max(), "chapas_perturbadas");
    config.busca.max_reinicios = inteiro_opcao(valores.at("max_reinicios"), numeric_limits<size_t>::max(), "max_reinicios");
    config.busca.max_avaliacoes_reparo = inteiro_opcao(valores.at("max_avaliacoes_reparo"), numeric_limits<size_t>::max(), "max_avaliacoes_reparo");
    config.rls.max_avaliacoes = inteiro_opcao(valores.at("rls_max_avaliacoes"), 100000000, "rls_max_avaliacoes");
    if (config.busca.chapas_perturbadas < 2 || config.rls.max_avaliacoes == 0) throw invalid_argument("Configuração exige chapas_perturbadas >= 2 e rls_max_avaliacoes >= 1.");
    return config;
}

ResultadoExecucao executa_metodo(const Instancia& instancia, const OpcoesExecucao& opcoes, const ConfigExperimento& config) {
    ResultadoExecucao resultado;
    resultado.metodo = opcoes.metodo;
    if (opcoes.metodo == "Hbase") resultado.busca = executa_hbase(instancia, opcoes.semente, opcoes.limite_cpu, config.busca);
    else if (opcoes.metodo == "Hext") resultado.busca = executa_hext(instancia, opcoes.semente, opcoes.limite_cpu, config.busca);
    else if (opcoes.metodo == "Hint") resultado.busca = executa_hint(instancia, opcoes.semente, opcoes.limite_cpu, config.busca);
    else if (opcoes.metodo == "Hcomb") resultado.busca = executa_hcomb(instancia, opcoes.semente, opcoes.limite_cpu, config.busca);
    else if (opcoes.metodo == "Haleat") resultado.busca = executa_haleat(instancia, opcoes.semente, opcoes.limite_cpu, config.busca);
    else if (opcoes.metodo == "RLS-f7") resultado.rls = executa_rls(instancia, opcoes.semente, opcoes.limite_cpu, config.rls);
    else throw invalid_argument("Método desconhecido: " + opcoes.metodo);
    return resultado;
}

const Solucao& solucao_execucao(const ResultadoExecucao& resultado) {
    return resultado.metodo == "RLS-f7" ? resultado.rls.solucao : resultado.busca.solucao;
}

string nome_execucao(const OpcoesExecucao& opcoes, const ConfigExperimento& config) {
    string nome = filesystem::path(opcoes.instancia).stem().string();
    for (char& c : nome) if (!(c >= 'A' && c <= 'Z') && !(c >= 'a' && c <= 'z') && !(c >= '0' && c <= '9') && c != '_' && c != '-') c = '_';
    if (nome.empty()) nome = "instancia";
    return nome + "__" + opcoes.metodo + "__" + to_string(opcoes.semente) + "__" + config.id;
}

void confere_destino(const OpcoesExecucao& opcoes, const ConfigExperimento& config) {
    filesystem::path diretorio(opcoes.saida);
    if (filesystem::exists(diretorio) && !filesystem::is_directory(diretorio)) throw runtime_error("Diretório de saída inválido: " + opcoes.saida);
    string nome = nome_execucao(opcoes, config);
    for (string sufixo : {".csv", ".solucao.csv"}) {
        auto destino = diretorio / (nome + sufixo);
        if (filesystem::exists(destino) || filesystem::is_symlink(destino)) throw runtime_error("Saída já existe; escolha outro diretório: " + destino.string());
    }
}

string familia_instancia(string caminho) {
    string nome = filesystem::path(caminho).filename().string();
    if (regex_match(nome, regex("A([1-9]|[1-3][0-9]|4[0-3])\\.ins2D"))) return "A";
    if (regex_match(nome, regex("BENG(0[1-9]|10)\\.ins2D"))) return "BENG";
    if (regex_match(nome, regex("cl_(0[1-9]|10)_(020|040|060|080|100)_(0[1-9]|10)\\.ins2D"))) return "CLASS";
    return "OUTRA";
}

string numero_real(double valor) {
    ostringstream texto;
    texto.imbue(locale::classic());
    texto << setprecision(numeric_limits<double>::max_digits10) << valor;
    return texto.str();
}

string numero_f7(__uint128_t valor) {
    string texto;
    do { texto.push_back('0' + valor % 10); valor /= 10; } while (valor > 0);
    reverse(texto.begin(), texto.end());
    return texto;
}

string campo_csv(string texto) {
    if (texto.find_first_of(",\"\r\n") == string::npos) return texto;
    string escapado = "\"";
    for (char c : texto) { if (c == '"') escapado += '"'; escapado += c; }
    return escapado + '"';
}

string registra_execucao(const Instancia& instancia, const OpcoesExecucao& opcoes, const ConfigExperimento& config, const ResultadoExecucao& resultado) {
    bool rls = opcoes.metodo == "RLS-f7";
    bool externa = opcoes.metodo == "Hext" || opcoes.metodo == "Hcomb";
    bool interna = opcoes.metodo == "Hint" || opcoes.metodo == "Hcomb" || opcoes.metodo == "Haleat";
    if (!metodo_conhecido(opcoes.metodo) || resultado.metodo != opcoes.metodo || (rls ? resultado.rls.metodo : resultado.busca.metodo) != opcoes.metodo) throw invalid_argument("Método do resultado não corresponde à execução.");
    const auto& solucao = solucao_execucao(resultado);
    auto verificacao = verifica_solucao(instancia, solucao);
    if (!verificacao.valido) throw runtime_error("Resultado não será registrado: " + verificacao.erro);
    auto limites = rls ? resultado.rls.limites : resultado.busca.limites;
    int64_t k = static_cast<int64_t>(solucao.chapas.size());
    double tempo_total = rls ? resultado.rls.tempo_total : resultado.busca.tempo_total;
    double tempo_melhor = rls ? resultado.rls.tempo_melhor : resultado.busca.tempo_melhor;
    string parada = rls ? resultado.rls.motivo_parada : resultado.busca.motivo_parada;
    const auto& evolucao = rls ? resultado.rls.evolucao : resultado.busca.evolucao;
    if (limites.referencia != max(limites.por_area, limites.dell_amico) || limites.referencia <= 0 || k < limites.referencia) throw invalid_argument("Limites inconsistentes no resultado.");
    if (!isfinite(tempo_total) || !isfinite(tempo_melhor) || tempo_melhor < 0 || tempo_melhor > tempo_total || !isfinite(opcoes.limite_cpu) || opcoes.limite_cpu <= 0) throw invalid_argument("Tempos inconsistentes no resultado.");
    if (parada != "limite_inferior" && parada != "limite_cpu" && parada != (rls ? "limite_avaliacoes" : "orcamento_reparo")) throw invalid_argument("Motivo de parada inválido.");
    if ((parada == "limite_inferior") != (k == limites.referencia) || (parada == "limite_cpu" && tempo_total < opcoes.limite_cpu)) throw invalid_argument("Motivo de parada inconsistente.");
    if (evolucao.size() != 6) throw invalid_argument("Resultado sem os seis marcos de evolução.");
    vector<double> tempos{0.1, 1, 5, 10, 30, 60};
    int64_t anterior = numeric_limits<int64_t>::max();
    bool disponivel = false;
    for (size_t m = 0; m < evolucao.size(); m++) {
        auto marco = evolucao[m];
        if (marco.tempo != tempos[m] || (!marco.disponivel && disponivel)) throw invalid_argument("Marcos de evolução inválidos.");
        if (marco.disponivel) {
            if (marco.chapas < k || marco.chapas > anterior || !isfinite(marco.desvio) || marco.desvio != desvio_percentual(marco.chapas, limites.referencia)) throw invalid_argument("Evolução inconsistente com a solução final.");
            anterior = marco.chapas;
            disponivel = true;
        }
    }
    if (rls && (resultado.rls.avaliacoes == 0 || resultado.rls.avaliacoes > config.rls.max_avaliacoes || resultado.rls.area_perfil != area_perfil_superior(solucao.chapas.back(), instancia.largura, instancia.altura) || resultado.rls.f7 != calcula_f7(instancia.area_chapa, solucao.chapas.size(), resultado.rls.area_perfil))) throw invalid_argument("Avaliações, perfil ou f7 inconsistentes.");
    confere_destino(opcoes, config);
    vector<pair<string, string>> campos;
    auto campo = [&](string nome, string valor) { campos.push_back({nome, valor}); };
    campo("versao", "1");
    campo("instancia", filesystem::path(opcoes.instancia).stem().string());
    campo("caminho_instancia", opcoes.instancia);
    campo("familia", familia_instancia(opcoes.instancia));
    campo("metodo", opcoes.metodo);
    campo("controle_auxiliar", opcoes.metodo == "Haleat" ? "1" : "0");
    campo("semente", to_string(opcoes.semente));
    campo("config_id", config.id);
    campo("config_estado", config.estado);
    campo("config_arquivo", opcoes.configuracao);
    campo("chapas_perturbadas", to_string(config.busca.chapas_perturbadas));
    campo("max_reinicios", to_string(config.busca.max_reinicios));
    campo("max_avaliacoes_reparo", to_string(config.busca.max_avaliacoes_reparo));
    campo("rls_max_avaliacoes", to_string(config.rls.max_avaliacoes));
    campo("tentativas_basicas", rls ? "" : "8");
    campo("max_decodificacoes_extras", interna ? "16" : "0");
    campo("limite_cpu", numero_real(opcoes.limite_cpu));
    campo("LBarea", to_string(limites.por_area));
    campo("LBdmv", to_string(limites.dell_amico));
    campo("LBref", to_string(limites.referencia));
    campo("K", to_string(k));
    campo("desvio", numero_real(desvio_percentual(k, limites.referencia)));
    campo("tempo_total", numero_real(tempo_total));
    campo("tempo_melhor", numero_real(tempo_melhor));
    campo("alcancou_lb", k == limites.referencia ? "1" : "0");
    campo("limite_cpu_atingido", tempo_total >= opcoes.limite_cpu ? "1" : "0");
    campo("motivo_parada", parada);
    campo("avaliacoes", to_string(rls ? resultado.rls.avaliacoes : resultado.busca.avaliacoes));
    campo("unidade_avaliacoes", rls ? "f7" : "candidato_externo");
    campo("tentativas_reducao", rls ? "" : to_string(resultado.busca.tentativas_reducao));
    campo("reducoes_aceitas", rls ? "" : to_string(resultado.busca.reducoes_aceitas));
    campo("perturbacoes", rls ? "" : to_string(resultado.busca.perturbacoes));
    campo("historico_atualizacoes", externa ? to_string(resultado.busca.orientacao_externa.atualizacoes) : "");
    campo("historico_reinicios", externa ? to_string(resultado.busca.orientacao_externa.reinicios) : "");
    campo("movimentos_orientados", externa ? to_string(resultado.busca.orientacao_externa.movimentos_orientados) : "");
    campo("melhorias_orientadas", externa ? to_string(resultado.busca.orientacao_externa.melhorias_aceitas) : "");
    campo("ativacoes_internas", interna ? to_string(resultado.busca.orientacao_interna.ativacoes) : "");
    campo("decodificacoes_extras", interna ? to_string(resultado.busca.orientacao_interna.decodificacoes) : "");
    campo("melhorias_internas", interna ? to_string(resultado.busca.orientacao_interna.melhorias) : "");
    campo("empacotamentos_completos", interna ? to_string(resultado.busca.orientacao_interna.completos) : "");
    campo("f7", rls ? numero_f7(resultado.rls.f7) : "");
    campo("area_perfil", rls ? to_string(resultado.rls.area_perfil) : "");
    campo("trocas", rls ? to_string(resultado.rls.trocas) : "");
    campo("inversoes", rls ? to_string(resultado.rls.inversoes) : "");
    campo("aceitos_rls", rls ? to_string(resultado.rls.aceitos) : "");
    campo("melhorias_rls", rls ? to_string(resultado.rls.melhorias) : "");
    vector<string> sufixos{"0_1", "1", "5", "10", "30", "60"};
    for (size_t m = 0; m < evolucao.size(); m++) {
        campo("K_" + sufixos[m], evolucao[m].disponivel ? to_string(evolucao[m].chapas) : "");
        campo("desvio_" + sufixos[m], evolucao[m].disponivel ? numero_real(evolucao[m].desvio) : "");
    }
    string nome = nome_execucao(opcoes, config);
    string solucao_nome = opcoes.salvar_solucao ? nome + ".solucao.csv" : "";
    campo("validada", "1");
    campo("solucao_arquivo", solucao_nome);
    ostringstream conteudo;
    for (bool cabecalho : {true, false}) {
        for (size_t c = 0; c < campos.size(); c++) {
            if (c > 0) conteudo << ',';
            conteudo << campo_csv(cabecalho ? campos[c].first : campos[c].second);
        }
        conteudo << '\n';
    }
    filesystem::create_directories(opcoes.saida);
    if (opcoes.salvar_solucao) salva_solucao_csv(instancia, solucao, (filesystem::path(opcoes.saida) / solucao_nome).string());
    string caminho = (filesystem::path(opcoes.saida) / (nome + ".csv")).string();
    ofstream arquivo(caminho);
    if (!arquivo) throw runtime_error("Não foi possível abrir o resultado: " + caminho);
    arquivo << conteudo.str();
    arquivo.close();
    if (!arquivo) throw runtime_error("Falha ao gravar o resultado: " + caminho);
    return caminho;
}
