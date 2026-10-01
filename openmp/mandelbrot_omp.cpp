/* Mandelbrot — versao OpenMP (memoria compartilhada).
 * Compilar: g++ -O2 -fopenmp -o bin/mandelbrot_omp openmp/mandelbrot_omp.cpp
 * Executar: ./bin/mandelbrot_omp W H threads [static|dynamic|guided] [chunk] [reduction|atomic|critical]
 * Exemplo:  ./bin/mandelbrot_omp 1000 1000 6 dynamic 1 reduction
 */
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <omp.h>
using namespace std;

int main(int argc, char** argv) {
    int W = (argc > 1) ? atoi(argv[1]) : 1000;
    int H = (argc > 2) ? atoi(argv[2]) : 1000;
    int T = (argc > 3) ? atoi(argv[3]) : omp_get_max_threads();
    const char* pol = (argc > 4) ? argv[4] : "dynamic";
    int chunk = (argc > 5) ? atoi(argv[5]) : 1;
    const char* red = (argc > 6) ? argv[6] : "reduction";
    const int MAXIT = 1000;

    omp_set_num_threads(T);
    if (!strcmp(pol, "static"))       omp_set_schedule(omp_sched_static, chunk);
    else if (!strcmp(pol, "guided"))  omp_set_schedule(omp_sched_guided, chunk);
    else                              omp_set_schedule(omp_sched_dynamic, chunk);

    vector<long> hist(W*H);

    double t0 = omp_get_wtime();
    #pragma omp parallel for schedule(runtime)
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
    double t1 = omp_get_wtime();

    long soma = 0;
    if (!strcmp(red, "atomic")) {
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < W*H; i++) {
            #pragma omp atomic
            soma += hist[i];
        }
    } else if (!strcmp(red, "critical")) {
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < W*H; i++) {
            #pragma omp critical
            soma += hist[i];
        }
    } else {
        #pragma omp parallel for schedule(static) reduction(+:soma)
        for (int i = 0; i < W*H; i++) soma += hist[i];
    }
    double t2 = omp_get_wtime();

    printf("W=%d H=%d  checksum=%ld  tempo=%.6f s\n", W, H, soma, t2 - t0);
    printf("threads=%d schedule=%s chunk=%d reducao=%s t_lacos=%.6f t_soma=%.6f\n",
           T, pol, chunk, red, t1 - t0, t2 - t1);
    return 0;
}
