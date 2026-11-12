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

CronometroCpu::CronometroCpu(double segundos) {
    if (!isfinite(segundos) || segundos < 0) throw invalid_argument("Limite de CPU deve ser finito e não negativo.");
    inicio = tempo_cpu();
    limite = segundos;
}

double CronometroCpu::decorrido() { return tempo_cpu() - inicio; }
bool CronometroCpu::esgotado() { return decorrido() >= limite; }
void CronometroCpu::verifica() { if (esgotado()) throw TempoEsgotado(); }
void verifica_tempo(CronometroCpu* relogio) { if (relogio != nullptr) relogio->verifica(); }
