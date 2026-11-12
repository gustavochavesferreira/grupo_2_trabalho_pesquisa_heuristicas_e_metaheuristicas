CXX := g++
CPPFLAGS := -Iinclude
CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -Wpedantic

COMMON_OBJS := obj/apresentacao.o obj/instancia.o
OBJS := $(COMMON_OBJS) obj/main.o obj/test_inicio.o obj/test_instancia.o obj/metadados_instancia.o
DEPS := $(OBJS:.o=.d)
EXE := bin/tp3
TEST_EXE := bin/test_inicio
INSTANCE_TEST_EXE := bin/test_instancia

.PHONY: all test clean catalog catalog-test

all: $(EXE)

$(EXE): $(COMMON_OBJS) obj/main.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(TEST_EXE): $(COMMON_OBJS) obj/test_inicio.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(INSTANCE_TEST_EXE): obj/instancia.o obj/test_instancia.o | bin
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

test: $(EXE) $(TEST_EXE) $(INSTANCE_TEST_EXE)
	./$(TEST_EXE)
	./$(INSTANCE_TEST_EXE)
	./$(EXE)

clean:
	$(RM) $(EXE) $(TEST_EXE) $(INSTANCE_TEST_EXE) bin/metadados_instancia $(OBJS) $(DEPS)

-include $(DEPS)
