# Marco 1 — Paralelização do Conjunto de Mandelbrot

**Disciplina:** Programação Paralela (CCO085) — IESB 2026/2 — Prof. Rodrigo Gonçalves Pinto
**Problema:** nº 3 da lista — Conjunto de Mandelbrot
**Integrantes:** Yuri Victor de Oliveira e Silva · Gabriel
**Repositório:** `<url do repositório>`

---

## 1. O que o algoritmo faz

O programa varre uma imagem de `W × H` pixels. Cada pixel `(x, y)` é mapeado para um
ponto `c = cr + i·ci` do plano complexo, com `cr` variando linearmente em `[-2,5; 1,0]`
e `ci` em `[-1,25; 1,25]`. Para esse `c`, a sequência `z₀ = 0`, `zₙ₊₁ = zₙ² + c` é
iterada até que `|zₙ|² > 4` (o ponto escapou e não pertence ao conjunto) ou até
atingir o teto `MAXIT = 1000` (o ponto é tratado como pertencente ao conjunto).

O valor gravado em `hist[y·W + x]` é o **número de iterações até o escape**. Ao final,
o programa soma todas as posições do vetor e imprime esse somatório como checksum, que
é o gabarito de corretude, junto com o tempo do laço principal.

## 2. Complexidade assintótica

O custo do pixel `(x, y)` é `it(x, y) ≤ MAXIT`. O custo total é

```
T(W, H) = Σ_y Σ_x it(x, y)  =  O(W · H · MAXIT)
```

O limite superior `O(W·H·MAXIT)` é justo apenas para os pixels internos ao conjunto.
Para os externos, `it` é pequeno — tipicamente algumas dezenas de iterações. O custo
médio efetivo por pixel é, portanto, muito menor que `MAXIT`, mas a **variância entre
pixels é enorme**, e é justamente essa variância que domina o comportamento paralelo
do problema.

O consumo de memória é `O(W·H)` para o vetor `hist` (8 bytes por pixel).

## 3. Perfilamento

Instrumentação em `seq/mandelbrot_perf.cpp`: timers em torno de cada trecho do
baseline, sem alterar a lógica nem a entrada.

Comando: `./bin/mandelbrot_perf 1600 1600`

| Trecho | Tempo (s) | % do total |
|---|---|---|
| Alocação do vetor `hist` | `<preencher>` | `<preencher>` |
| **Laços do Mandelbrot** | `<preencher>` | `<preencher>` |
| Somatório do checksum | `<preencher>` | `<preencher>` |
| **Total** | `<preencher>` | 100 % |

**Hotspot:** o laço duplo sobre `y` e `x`, e dentro dele o laço `while` de iteração
complexa. É onde está praticamente todo o tempo do programa. A alocação e o somatório
final são lineares em `W·H` e sem trabalho aritmético relevante.

### 3.1 Evidência do desbalanceamento

O mesmo executável imprime o total de iteracões acumuladas por faixa de linhas da
imagem. O resultado mostra que as faixas centrais — onde está o corpo do conjunto —
custam várias vezes mais que as faixas superiores e inferiores:

| Faixa de linhas | Iterações acumuladas |
|---|---|
| `<preencher a partir da saída do mandelbrot_perf>` | |

Esse é o fato central do problema: **o trabalho não é uniforme no domínio**. Qualquer
divisão do domínio em blocos contíguos iguais entrega quantidades de trabalho muito
diferentes a cada unidade de processamento.

## 4. Baseline medido

**Máquina:** `<modelo do processador>`, `<n>` núcleos físicos / `<n>` threads lógicas,
`<RAM>`, `<distribuição Linux>` no contêiner Docker da disciplina.
**Compilador:** `g++ <versão>` com `-O2`.

**Protocolo de medição.** Cada configuração é executada quatro vezes: a primeira é
descartada (aquecimento de cache e de páginas de memória) e as três restantes têm a
**mediana** tomada como valor reportado. A mediana é preferida à média por ser
insensível a uma execução isolada perturbada por outro processo do sistema. Todas as
medições usam a mesma entrada determinística do baseline, o que torna as execuções
diretamente comparáveis. O tempo considerado é o do laço principal mais o somatório,
como reportado pelo próprio programa.

| Entrada (W × H) | Tempo mediano (s) | Mín (s) | Máx (s) | Checksum |
|---|---|---|---|---|
| 600 × 600 | `<preencher>` | | | `<preencher>` |
| 1000 × 1000 | `<preencher>` | | | `<preencher>` |
| 1600 × 1600 | `<preencher>` | | | `<preencher>` |
| 2200 × 2200 | `<preencher>` | | | `<preencher>` |

O tempo cresce aproximadamente com `W·H`, como esperado da análise assintótica.

## 5. Fração paralelizável e Lei de Amdahl

A parte inerentemente sequencial do programa é a alocação e inicialização do vetor
`hist`. Os laços do Mandelbrot são totalmente independentes entre pixels — não há
dependência de dados entre iterações — e o somatório do checksum é uma redução, que
é paralelizável em `O(log P)` passos.

Com `p` a fração paralelizável medida no perfilamento:

```
p = (t_laços + t_somatório) / t_total = <preencher>
S_max = 1 / (1 - p) = <preencher>
```

Para `P` unidades de processamento, o speedup previsto é

```
S(P) = 1 / ( (1 - p) + p/P )
```

| P | S(P) previsto por Amdahl |
|---|---|
| 2 | `<preencher>` |
| 4 | `<preencher>` |
| 6 | `<preencher>` |
| 12 | `<preencher>` |

**Observação crítica.** A fração serial medida é muito pequena, de modo que Amdahl
prevê um speedup quase linear. Isso significa que o afastamento que será observado no
Marco 2 **não virá da fração serial**. As causas esperadas são outras: desbalanceamento
de carga, overhead de escalonamento dinâmico, custo de comunicação em MPI e, nos
tamanhos maiores, limite de banda de memória. Amdahl aqui funciona como teto teórico
otimista, não como explicação do resultado.

## 6. Plano de paralelização

### 6.1 OpenMP

- **Padrão:** laço paralelo sobre as linhas (`y`), com `#pragma omp parallel for`.
  A granularidade de uma linha inteira já é grande o bastante para amortizar o custo
  de despacho, e evita o overhead de paralelizar o laço interno.
- **Variáveis privadas:** `cr`, `ci`, `zr`, `zi` e `it` são declaradas *dentro* do
  corpo do laço, o que as torna automaticamente privadas a cada thread. Essa é a
  origem da única condição de corrida possível no laço principal: se fossem declaradas
  fora, seriam compartilhadas e o resultado seria não determinístico.
- **Escrita em `hist`:** cada iteração escreve em `hist[y·W + x]`, um índice distinto
  por pixel. Não há corrida e não é necessário nenhum mecanismo de exclusão. Como
  threads diferentes trabalham em linhas diferentes e uma linha ocupa `W · 8` bytes,
  o compartilhamento falso de linha de cache é desprezível.
- **Checksum:** é uma redução sobre uma variável compartilhada e exige tratamento.
  Serão comparados os três mecanismos — `reduction(+:soma)`, `atomic` e `critical` —
  com o tempo do somatório medido separadamente, para justificar a escolha com
  evidência e não por convenção.
- **Escalonamento:** dado o desbalanceamento demonstrado na seção 3.1, espera-se que
  `static` seja a pior política. Serão comparadas `static`, `dynamic` e `guided` com
  chunks 1, 10 e padrão, medindo o tempo de cada combinação.
- **Curva de speedup** para 1, 2, 4, 6, 8 e 12 threads, validada contra o checksum
  do baseline em cada ponto.

### 6.2 MPI

- **Decomposição:** de domínio, por linhas da imagem. Cada processo calcula um
  subconjunto das linhas e nenhum precisa de dados dos vizinhos — o Mandelbrot não
  tem dependência espacial, diferentemente de um stencil. Não há troca de halo.
- **Duas variantes, deliberadamente:** distribuição em **blocos contíguos** e
  distribuição **cíclica** (o processo `r` fica com as linhas `r`, `r+P`, `r+2P`, …).
  A variante em blocos serve para medir o desbalanceamento; a cíclica para mostrar
  que a intercalação distribui linhas caras e baratas de forma quase uniforme entre
  os processos, sem custo adicional de comunicação.
- **Coletivas:** `MPI_Gatherv` reúne no processo 0 as linhas calculadas por todos
  (os blocos têm tamanhos diferentes quando `H` não é múltiplo de `P`, o que exige
  a variante `v` com `counts` e `displs`); `MPI_Reduce` com `MPI_MAX` e `MPI_MIN`
  coleta os tempos de cálculo de cada processo, o que quantifica o desbalanceamento
  diretamente.
- **Overhead de comunicação:** medido isoladamente em torno do `MPI_Gatherv` e
  reportado em função do número de processos. O volume transferido é fixo (`W·H·8`
  bytes) e independe de `P`, o que deve tornar a comunicação uma fração crescente do
  tempo total conforme o cálculo encolhe.
- **Curva de speedup** para `-np` 1, 2, 4, 6, 8 e 12, validada contra o checksum do
  baseline em cada ponto.

### 6.3 Hipóteses a verificar no Marco 2

1. `dynamic` supera `static` de forma clara, e a vantagem cresce com o número de threads.
2. A decomposição cíclica em MPI aproxima o desbalanceamento de zero, enquanto a
   decomposição em blocos mantém desbalanceamento alto e independente de `P`.
3. A eficiência cai ao passar dos núcleos físicos para as threads lógicas (SMT), já
   que o laço é limitado por unidades de ponto flutuante e não por latência de memória.
4. O speedup real fica abaixo do previsto por Amdahl, e a diferença é explicada por
   desbalanceamento e overhead, não pela fração serial.
