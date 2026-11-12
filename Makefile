CXX := g++
CPPFLAGS := -Iinclude
CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -Wpedantic

COMMON_OBJS := obj/apresentacao.o obj/instancia.o obj/solucao.o obj/verificador_solucao.o obj/geometria.o obj/decodificador.o obj/empacotador_base.o obj/construcao_inicial.o
OBJS := $(COMMON_OBJS) obj/main.o obj/test_inicio.o obj/test_instancia.o obj/test_solucao.o obj/test_decodificador.o obj/test_empacotador_base.o obj/test_construcao_inicial.o obj/metadados_instancia.o
DEPS := $(OBJS:.o=.d)
EXE := bin/tp3
TEST_EXE := bin/test_inicio
INSTANCE_TEST_EXE := bin/test_instancia
SOLUTION_TEST_EXE := bin/test_solucao
DECODER_TEST_EXE := bin/test_decodificador
PACKER_TEST_EXE := bin/test_empacotador_base
CONSTRUCTION_TEST_EXE := bin/test_construcao_inicial

.PHONY: all test clean catalog catalog-test

all: $(EXE)

$(EXE): $(COMMON_OBJS) obj/main.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(TEST_EXE): $(COMMON_OBJS) obj/test_inicio.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(INSTANCE_TEST_EXE): obj/instancia.o obj/test_instancia.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(SOLUTION_TEST_EXE): obj/instancia.o obj/solucao.o obj/verificador_solucao.o obj/test_solucao.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(DECODER_TEST_EXE): obj/instancia.o obj/geometria.o obj/decodificador.o obj/verificador_solucao.o obj/test_decodificador.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(PACKER_TEST_EXE): obj/instancia.o obj/geometria.o obj/decodificador.o obj/empacotador_base.o obj/verificador_solucao.o obj/test_empacotador_base.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(CONSTRUCTION_TEST_EXE): obj/instancia.o obj/geometria.o obj/decodificador.o obj/construcao_inicial.o obj/verificador_solucao.o obj/test_construcao_inicial.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

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

test: $(EXE) $(TEST_EXE) $(INSTANCE_TEST_EXE) $(SOLUTION_TEST_EXE) $(DECODER_TEST_EXE) $(PACKER_TEST_EXE) $(CONSTRUCTION_TEST_EXE)
	./$(TEST_EXE)
	./$(INSTANCE_TEST_EXE)
	./$(SOLUTION_TEST_EXE)
	./$(DECODER_TEST_EXE)
	./$(PACKER_TEST_EXE)
	./$(CONSTRUCTION_TEST_EXE)
	./$(EXE)

clean:
	$(RM) $(EXE) $(TEST_EXE) $(INSTANCE_TEST_EXE) $(SOLUTION_TEST_EXE) $(DECODER_TEST_EXE) $(PACKER_TEST_EXE) $(CONSTRUCTION_TEST_EXE) bin/metadados_instancia $(OBJS) $(DEPS)

-include $(DEPS)
