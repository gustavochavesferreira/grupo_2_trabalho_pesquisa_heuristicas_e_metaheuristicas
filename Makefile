CXX := g++
CPPFLAGS := -Iinclude
CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -Wpedantic

COMMON_OBJS := obj/apresentacao.o
OBJS := $(COMMON_OBJS) obj/main.o obj/test_inicio.o
DEPS := $(OBJS:.o=.d)
EXE := bin/tp3
TEST_EXE := bin/test_inicio

.PHONY: all test clean

all: $(EXE)

$(EXE): $(COMMON_OBJS) obj/main.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(TEST_EXE): $(COMMON_OBJS) obj/test_inicio.o | bin
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

obj/%.o: src/%.cpp | obj
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c -o $@ $<

obj/test_inicio.o: tests/test_inicio.cpp | obj
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c -o $@ $<

bin obj:
	mkdir -p $@

test: $(EXE) $(TEST_EXE)
	./$(TEST_EXE)
	./$(EXE)

clean:
	$(RM) $(EXE) $(TEST_EXE) $(OBJS) $(DEPS)

-include $(DEPS)
