# Paralelização do Conjunto de Mandelbrot — CCO085 (2026/2)

Projeto Acadêmico de Programação Paralela — IESB, Campus Asa Sul
Prof. Rodrigo Gonçalves Pinto · Problema 3 da lista: **Conjunto de Mandelbrot**

Integrantes: Yuri Victor de Oliveira e Silva · Gabriel Vieira

O baseline sequencial fornecido pelo professor está em `seq/mandelbrot_seq.cpp`, sem
nenhuma alteração de lógica ou de entrada. As versões OpenMP e MPI partem dele e
produzem **exatamente o mesmo checksum** para a mesma entrada.

## Estrutura

```
seq/mandelbrot_seq.cpp     baseline do professor (intocado)
seq/mandelbrot_perf.cpp    baseline + timers por trecho, para o perfilamento
openmp/mandelbrot_omp.cpp  versão de memória compartilhada
mpi/mandelbrot_mpi.cpp     versão de memória distribuída
scripts/medir.py           roda os experimentos e grava dados/medicoes.csv
scripts/graficos.py        gera os gráficos em dados/graficos/
dados/                     medições em CSV e gráficos gerados
docs/                      relatório do Marco 2 — análise experimental
```

## Requisitos

Linux com `g++` (suporte a OpenMP), OpenMPI (`mpicxx`, `mpirun`) e Python 3 com
`matplotlib`. No ambiente da disciplina tudo isso já vem pronto.

```bash
sudo apt install -y build-essential libopenmpi-dev openmpi-bin python3-pip
pip3 install matplotlib --break-system-packages
```

Confira o número de núcleos disponíveis antes de medir:

```bash
nproc
```

## Compilar

```bash
make
```

Gera os quatro executáveis em `bin/`.

## Rodar

```bash
# baseline (gabarito)
./bin/mandelbrot_seq 2200 2200

# perfilamento por trecho, com a estimativa de Amdahl
./bin/mandelbrot_perf 1600 1600

# OpenMP: W H threads [static|dynamic|guided] chunk [reduction|atomic|critical]
./bin/mandelbrot_omp 2200 2200 12 dynamic 1 reduction

# MPI: W H [bloco|ciclico]
mpirun -np 8 ./bin/mandelbrot_mpi 2200 2200 ciclico
```

Teste rápido de que as três versões rodam e os checksums batem:

```bash
make testar
```

## Reproduzir as medições e os gráficos

```bash
python3 scripts/medir.py       # bateria completa
python3 scripts/graficos.py
```

`medir.py` descarta a primeira execução (aquecimento), repete cada configuração
três vezes, usa a mediana, grava `dados/medicoes.csv` e ao final confere se todos
os checksums batem com o do baseline para o mesmo tamanho de entrada. O cronômetro
está dentro dos próprios programas em C++ (`clock_gettime`, `omp_get_wtime`,
`MPI_Wtime`); o script apenas executa os binários e consolida o CSV.

## Validação de corretude

O baseline define o resultado correto. Checksums de referência:

| Entrada | Checksum |
|---|---|
| 600 × 600 | 63906087 |
| 1000 × 1000 | 177507041 |
| 1600 × 1600 | 454328600 |
| 2200 × 2200 | 858878868 |

As **136 execuções** registradas em `dados/medicoes.csv` reproduzem esses valores
para qualquer número de threads ou processos, qualquer política de escalonamento,
qualquer mecanismo de redução e qualquer decomposição.

## Resultados principais

Máquina de referência: Intel Core i5-11400F (6 núcleos físicos, 12 threads lógicas),
Ubuntu sobre WSL2, `g++ -O2` e OpenMPI.

| Métrica | Valor |
|---|---|
| Fração paralelizável medida (1600²) | 0,992634 |
| Speedup máximo por Amdahl com 12 unidades | 11,10 |
| Melhor speedup OpenMP (1600², 12 threads) | **10,40** |
| Melhor speedup MPI (2200², 12 processos, cíclico) | **8,66** |
| Pior política de escalonamento (`static,0`) | 4,34 |
| Melhor política (`dynamic,1`) | 9,92 |
| Desbalanceamento MPI em bloco, 4 processos | 93,71 % |
| Desbalanceamento MPI cíclico, 4 processos | 0,78 % |

A discussão completa — perfilamento, comparação de políticas, tratamento da condição
de corrida, decomposição de domínio, escalabilidade forte e fraca e o afastamento em
relação à Lei de Amdahl — está em `docs/Marco2_Analise_Experimental.pdf`.
