CXX := g++
CPPFLAGS := -Iinclude
CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -Wpedantic

COMMON_OBJS := obj/apresentacao.o obj/instancia.o obj/solucao.o obj/verificador_solucao.o obj/geometria.o obj/decodificador.o obj/empacotador_base.o obj/construcao_inicial.o obj/limites_inferiores.o obj/estado_reparo.o obj/vnd.o obj/tempo_cpu.o obj/hbase.o obj/orientacao_externa.o obj/orientacao_interna.o obj/decodificador_ibl.o obj/rls.o obj/evolucao.o obj/experimento.o
OBJS := $(COMMON_OBJS) obj/main.o obj/test_inicio.o obj/test_instancia.o obj/test_solucao.o obj/test_decodificador.o obj/test_empacotador_base.o obj/test_construcao_inicial.o obj/test_limites_inferiores.o obj/test_estado_reparo.o obj/test_vnd.o obj/test_hbase.o obj/test_hext.o obj/test_hint.o obj/test_haleat.o obj/test_hcomb.o obj/test_ibl.o obj/test_rls.o obj/test_experimento.o obj/test_integracao.o obj/metadados_instancia.o
DEPS := $(OBJS:.o=.d)
EXE := bin/tp3
TEST_EXE := bin/test_inicio
INSTANCE_TEST_EXE := bin/test_instancia
SOLUTION_TEST_EXE := bin/test_solucao
DECODER_TEST_EXE := bin/test_decodificador
PACKER_TEST_EXE := bin/test_empacotador_base
CONSTRUCTION_TEST_EXE := bin/test_construcao_inicial
BOUNDS_TEST_EXE := bin/test_limites_inferiores
REPAIR_TEST_EXE := bin/test_estado_reparo
VND_TEST_EXE := bin/test_vnd
HBASE_TEST_EXE := bin/test_hbase
HEXT_TEST_EXE := bin/test_hext
HINT_TEST_EXE := bin/test_hint
HALEAT_TEST_EXE := bin/test_haleat
HCOMB_TEST_EXE := bin/test_hcomb
IBL_TEST_EXE := bin/test_ibl
RLS_TEST_EXE := bin/test_rls
EXPERIMENT_TEST_EXE := bin/test_experimento
INTEGRATION_TEST_EXE := bin/test_integracao

.PHONY: all test clean catalog catalog-test integration-test orchestration-test informacoes-build

all: $(EXE)

$(EXE): $(COMMON_OBJS) obj/main.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(TEST_EXE): $(COMMON_OBJS) obj/test_inicio.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(INSTANCE_TEST_EXE): obj/instancia.o obj/test_instancia.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(SOLUTION_TEST_EXE): obj/instancia.o obj/solucao.o obj/verificador_solucao.o obj/test_solucao.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(DECODER_TEST_EXE): obj/instancia.o obj/geometria.o obj/decodificador.o obj/verificador_solucao.o obj/test_decodificador.o obj/tempo_cpu.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(PACKER_TEST_EXE): obj/instancia.o obj/geometria.o obj/decodificador.o obj/empacotador_base.o obj/verificador_solucao.o obj/test_empacotador_base.o obj/tempo_cpu.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(CONSTRUCTION_TEST_EXE): obj/instancia.o obj/geometria.o obj/decodificador.o obj/construcao_inicial.o obj/verificador_solucao.o obj/test_construcao_inicial.o obj/tempo_cpu.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(BOUNDS_TEST_EXE): obj/instancia.o obj/limites_inferiores.o obj/test_limites_inferiores.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(REPAIR_TEST_EXE): obj/instancia.o obj/geometria.o obj/decodificador.o obj/empacotador_base.o obj/construcao_inicial.o obj/estado_reparo.o obj/verificador_solucao.o obj/test_estado_reparo.o obj/tempo_cpu.o obj/orientacao_externa.o obj/orientacao_interna.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(VND_TEST_EXE): obj/instancia.o obj/geometria.o obj/decodificador.o obj/empacotador_base.o obj/construcao_inicial.o obj/estado_reparo.o obj/verificador_solucao.o obj/vnd.o obj/test_vnd.o obj/tempo_cpu.o obj/orientacao_externa.o obj/orientacao_interna.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(HBASE_TEST_EXE): $(COMMON_OBJS) obj/test_hbase.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(HEXT_TEST_EXE): $(COMMON_OBJS) obj/test_hext.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(HINT_TEST_EXE): $(COMMON_OBJS) obj/test_hint.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(HALEAT_TEST_EXE): $(COMMON_OBJS) obj/test_haleat.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(HCOMB_TEST_EXE): $(COMMON_OBJS) obj/test_hcomb.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(IBL_TEST_EXE): obj/instancia.o obj/verificador_solucao.o obj/tempo_cpu.o obj/decodificador_ibl.o obj/test_ibl.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(RLS_TEST_EXE): obj/instancia.o obj/verificador_solucao.o obj/tempo_cpu.o obj/decodificador_ibl.o obj/limites_inferiores.o obj/rls.o obj/evolucao.o obj/test_rls.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(EXPERIMENT_TEST_EXE): $(COMMON_OBJS) obj/test_experimento.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(INTEGRATION_TEST_EXE): $(COMMON_OBJS) obj/test_integracao.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

integration-test: $(EXE) $(INTEGRATION_TEST_EXE)
	./$(INTEGRATION_TEST_EXE)
	python3 tests/test_integracao_cli.py

obj/%.o: src/%.cpp | obj
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c -o $@ $<

obj/test_%.o: tests/test_%.cpp | obj
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c -o $@ $<

bin obj:
	mkdir -p $@

obj/metadados_instancia.o: scripts/metadados_instancia.cpp | obj
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c -o $@ $<

bin/metadados_instancia: obj/instancia.o obj/metadados_instancia.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

catalog: bin/metadados_instancia
	python3 scripts/catalogar_instancias.py

catalog-test: bin/metadados_instancia
	python3 tests/test_catalogo.py

test: $(EXE) $(TEST_EXE) $(INSTANCE_TEST_EXE) $(SOLUTION_TEST_EXE) $(DECODER_TEST_EXE) $(PACKER_TEST_EXE) $(CONSTRUCTION_TEST_EXE) $(BOUNDS_TEST_EXE) $(REPAIR_TEST_EXE) $(VND_TEST_EXE) $(HBASE_TEST_EXE) $(HEXT_TEST_EXE) $(HINT_TEST_EXE) $(HALEAT_TEST_EXE) $(HCOMB_TEST_EXE) $(IBL_TEST_EXE) $(RLS_TEST_EXE) $(EXPERIMENT_TEST_EXE)
	./$(TEST_EXE)
	./$(INSTANCE_TEST_EXE)
	./$(SOLUTION_TEST_EXE)
	./$(DECODER_TEST_EXE)
	./$(PACKER_TEST_EXE)
	./$(CONSTRUCTION_TEST_EXE)
	./$(BOUNDS_TEST_EXE)
	./$(REPAIR_TEST_EXE)
	./$(VND_TEST_EXE)
	./$(HBASE_TEST_EXE)
	./$(HEXT_TEST_EXE)
	./$(HINT_TEST_EXE)
	./$(HALEAT_TEST_EXE)
	./$(HCOMB_TEST_EXE)
	./$(IBL_TEST_EXE)
	./$(RLS_TEST_EXE)
	./$(EXPERIMENT_TEST_EXE)
	python3 tests/test_cli.py
	./$(EXE)

clean:
	$(RM) $(EXE) $(TEST_EXE) $(INSTANCE_TEST_EXE) $(SOLUTION_TEST_EXE) $(DECODER_TEST_EXE) $(PACKER_TEST_EXE) $(CONSTRUCTION_TEST_EXE) $(BOUNDS_TEST_EXE) $(REPAIR_TEST_EXE) $(VND_TEST_EXE) $(HBASE_TEST_EXE) $(HEXT_TEST_EXE) $(HINT_TEST_EXE) $(HALEAT_TEST_EXE) $(HCOMB_TEST_EXE) $(IBL_TEST_EXE) $(RLS_TEST_EXE) $(EXPERIMENT_TEST_EXE) $(INTEGRATION_TEST_EXE) bin/metadados_instancia $(OBJS) $(DEPS)

-include $(DEPS)

# As mesmas variáveis usadas na compilação são registradas pelo orquestrador.
informacoes-build:
	@echo "CXX=$(CXX)"
	@echo "CPPFLAGS=$(CPPFLAGS)"
	@echo "CXXFLAGS=$(CXXFLAGS)"
	@echo "LDFLAGS=$(LDFLAGS)"
	@echo "LDLIBS=$(LDLIBS)"

orchestration-test: $(EXE)
	python3 tests/test_orquestracao.py
