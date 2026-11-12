#ifndef TEMPO_CPU_H
#define TEMPO_CPU_H

#include <stdexcept>

using namespace std;

class TempoEsgotado : public runtime_error {
    public:
        TempoEsgotado();
};

class CronometroCpu {
    public:
        double inicio;
        double limite;
        CronometroCpu(double segundos);
        double decorrido();
        bool esgotado();
        void verifica();
};

double tempo_cpu();
void verifica_tempo(CronometroCpu* relogio);

#endif
