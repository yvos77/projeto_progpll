# Autores e frentes de responsabilidade

Disciplina: Programação Paralela (CCO085) — IESB 2026/2
Problema 3 — Conjunto de Mandelbrot
Repositório: https://github.com/yvos77/projeto_progpll

O grupo foi formado originalmente por três integrantes. Com a mudança de turma de
um dos integrantes, o trabalho foi conduzido em dupla, com autorização do professor.
As três frentes previstas no enunciado foram mantidas e redistribuídas.

| Integrante | Frente |
|---|---|
| Yuri Victor de Oliveira e Silva | Baseline e perfilamento · Versão OpenMP |
| Gabriel Vieira | Versão MPI |

## Frente 1 — Baseline e perfilamento

- Análise de complexidade do algoritmo sequencial fornecido
- Instrumentação por trecho (`seq/mandelbrot_perf.cpp`) e identificação dos hotspots
- Estimativa da fração paralelizável e do speedup máximo pela Lei de Amdahl
- Protocolo de medição: repetições, descarte de aquecimento, tamanhos de entrada

## Frente 2 — OpenMP (memória compartilhada)

- Paralelização do laço externo com `#pragma omp parallel for`
- Tratamento de condições de corrida e comparação medida entre `reduction`,
  `atomic` e `critical` no somatório do checksum
- Comparação das políticas `static`, `dynamic` e `guided` com variação de chunk
- Curva de speedup e de eficiência por número de threads

## Frente 3 — MPI (memória distribuída)

- Decomposição de domínio por linhas, em duas variantes: blocos contíguos e cíclica
- Coletivas: `MPI_Gatherv` para reunir a imagem e `MPI_Reduce` para os tempos
- Medição do overhead de comunicação em função do número de processos
- Curva de speedup por número de processos