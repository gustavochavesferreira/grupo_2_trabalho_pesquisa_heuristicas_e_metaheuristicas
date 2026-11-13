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
    private:
        // Última leitura exata da CPU do processo e o relógio de parede no mesmo instante.
        // Como o processo é monothread, a CPU não avança mais que o tempo de parede:
        // enquanto cpu_lida + (parede_agora - parede_lida) < limite, o prazo certamente
        // não foi atingido e a chamada de sistema da CPU pode ser evitada.
        double cpu_lida;
        double parede_lida;
};

double tempo_cpu();
double tempo_parede();
void verifica_tempo(CronometroCpu* relogio);

#endif
