#include "tempo_cpu.h"

#include <cmath>
#include <ctime>

using namespace std;

TempoEsgotado::TempoEsgotado() : runtime_error("Limite de CPU atingido.") {}

double tempo_cpu() {
    timespec valor;
    if (clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &valor) != 0) throw runtime_error("Falha ao consultar CPU do processo.");
    return valor.tv_sec + valor.tv_nsec / 1000000000.0;
}

double tempo_parede() {
    // CLOCK_MONOTONIC é atendido pelo vDSO, sem chamada de sistema.
    timespec valor;
    if (clock_gettime(CLOCK_MONOTONIC, &valor) != 0) throw runtime_error("Falha ao consultar o relógio monotônico.");
    return valor.tv_sec + valor.tv_nsec / 1000000000.0;
}

CronometroCpu::CronometroCpu(double segundos) {
    if (!isfinite(segundos) || segundos < 0) throw invalid_argument("Limite de CPU deve ser finito e não negativo.");
    inicio = tempo_cpu();
    limite = segundos;
    cpu_lida = inicio;
    parede_lida = tempo_parede();
}

double CronometroCpu::decorrido() {
    parede_lida = tempo_parede();
    cpu_lida = tempo_cpu();
    return cpu_lida - inicio;
}

bool CronometroCpu::esgotado() {
    // Limite superior da CPU atual sem consultar o kernel. Se ele ainda está abaixo do
    // prazo, a leitura exata também estaria; caso contrário, consulta a CPU de fato.
    // A decisão é idêntica à da leitura exata em toda chamada.
    double cota = (cpu_lida - inicio) + (tempo_parede() - parede_lida);
    if (cota < limite) return false;
    return decorrido() >= limite;
}

void CronometroCpu::verifica() { if (esgotado()) throw TempoEsgotado(); }
void verifica_tempo(CronometroCpu* relogio) { if (relogio != nullptr) relogio->verifica(); }
