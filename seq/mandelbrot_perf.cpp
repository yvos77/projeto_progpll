/* Mandelbrot — baseline instrumentado para perfilamento por trecho.
 * A logica de calculo e a entrada sao identicas ao baseline do professor.
 * Compilar: g++ -O2 -o bin/mandelbrot_perf seq/mandelbrot_perf.cpp
 * Executar: ./bin/mandelbrot_perf 1000 1000
 */
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <ctime>
using namespace std;

static double agora() {
    timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(int argc, char** argv) {
    int W = (argc > 1) ? atoi(argv[1]) : 1000;
    int H = (argc > 2) ? atoi(argv[2]) : 1000;
    const int MAXIT = 1000;

    double ta = agora();
    vector<long> hist(W*H);
    double tb = agora();

    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            double cr = -2.5 + 3.5 * x / W;
            double ci = -1.25 + 2.5 * y / H;
            double zr = 0, zi = 0; int it = 0;
            while (zr*zr + zi*zi <= 4.0 && it < MAXIT) {
                double t = zr*zr - zi*zi + cr;
                zi = 2*zr*zi + ci; zr = t; it++;
            }
            hist[y*W + x] = it;
        }
    double tc = agora();

    long soma = 0;
    for (int i = 0; i < W*H; i++) soma += hist[i];
    double td = agora();

    double t_aloc = tb - ta, t_lacos = tc - tb, t_soma = td - tc, t_tot = td - ta;

    printf("W=%d H=%d  checksum=%ld  tempo=%.6f s\n", W, H, soma, t_lacos);
    printf("\n--- perfilamento por trecho ---\n");
    printf("%-28s %12s %8s\n", "trecho", "tempo (s)", "%");
    printf("%-28s %12.6f %7.2f%%\n", "alocacao do vetor", t_aloc, 100.0*t_aloc/t_tot);
    printf("%-28s %12.6f %7.2f%%\n", "lacos do Mandelbrot", t_lacos, 100.0*t_lacos/t_tot);
    printf("%-28s %12.6f %7.2f%%\n", "somatorio do checksum", t_soma, 100.0*t_soma/t_tot);
    printf("%-28s %12.6f %7.2f%%\n", "TOTAL", t_tot, 100.0);
    printf("\nfracao paralelizavel estimada p = %.6f\n", (t_lacos + t_soma) / t_tot);
    printf("speedup maximo por Amdahl (P->inf) = %.2f\n", t_tot / t_aloc);

    printf("\n--- custo por faixa de linhas (evidencia de desbalanceamento) ---\n");
    int faixas = 10, passo = H / faixas;
    for (int f = 0; f < faixas; f++) {
        long acc = 0;
        for (int y = f*passo; y < (f+1)*passo && y < H; y++)
            for (int x = 0; x < W; x++) acc += hist[y*W + x];
        printf("linhas %5d-%5d  iteracoes=%12ld\n", f*passo, (f+1)*passo - 1, acc);
    }
    return 0;
}
