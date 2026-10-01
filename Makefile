CXX      := g++
MPICXX   := mpicxx
CXXFLAGS := -O2 -Wall
OMPFLAGS := -fopenmp
BIN      := bin

.PHONY: all limpar testar

all: $(BIN)/mandelbrot_seq $(BIN)/mandelbrot_perf $(BIN)/mandelbrot_omp $(BIN)/mandelbrot_mpi

$(BIN):
	mkdir -p $(BIN)

$(BIN)/mandelbrot_seq: seq/mandelbrot_seq.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BIN)/mandelbrot_perf: seq/mandelbrot_perf.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BIN)/mandelbrot_omp: openmp/mandelbrot_omp.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) -o $@ $<

$(BIN)/mandelbrot_mpi: mpi/mandelbrot_mpi.cpp | $(BIN)
	$(MPICXX) $(CXXFLAGS) -o $@ $<

testar: all
	@./$(BIN)/mandelbrot_seq 600 600
	@./$(BIN)/mandelbrot_omp 600 600 4 dynamic 1 reduction
	@mpirun --oversubscribe -np 4 ./$(BIN)/mandelbrot_mpi 600 600 ciclico

limpar:
	rm -rf $(BIN)
