/* Mandelbrot — versao MPI (memoria distribuida).
 * Compilar: mpicxx -O2 -o bin/mandelbrot_mpi mpi/mandelbrot_mpi.cpp
 * Executar: mpirun -np 4 ./bin/mandelbrot_mpi W H [bloco|ciclico]
 * Exemplo:  mpirun -np 4 ./bin/mandelbrot_mpi 1000 1000 ciclico
 */
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <mpi.h>
using namespace std;

static void linhas_do_rank(int r, int H, int size, bool ciclico, vector<int>& out) {
    out.clear();
    if (ciclico) {
        for (int y = r; y < H; y += size) out.push_back(y);
    } else {
        int base = H / size, resto = H % size;
        int inicio = r * base + (r < resto ? r : resto);
        int n = base + (r < resto ? 1 : 0);
        for (int k = 0; k < n; k++) out.push_back(inicio + k);
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int W = (argc > 1) ? atoi(argv[1]) : 1000;
    int H = (argc > 2) ? atoi(argv[2]) : 1000;
    bool ciclico = (argc > 3) ? (strcmp(argv[3], "ciclico") == 0) : true;
    const int MAXIT = 1000;

    vector<int> minhas;
    linhas_do_rank(rank, H, size, ciclico, minhas);
    vector<long> local((size_t)minhas.size() * W);

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();

    for (size_t k = 0; k < minhas.size(); k++) {
        int y = minhas[k];
        for (int x = 0; x < W; x++) {
            double cr = -2.5 + 3.5 * x / W;
            double ci = -1.25 + 2.5 * y / H;
            double zr = 0, zi = 0; int it = 0;
            while (zr*zr + zi*zi <= 4.0 && it < MAXIT) {
                double t = zr*zr - zi*zi + cr;
                zi = 2*zr*zi + ci; zr = t; it++;
            }
            local[k*W + x] = it;
        }
    }
    double t_calc = MPI_Wtime() - t0;

    vector<int> counts(size), displs(size);
    vector<int> tmp;
    int acc = 0;
    for (int r = 0; r < size; r++) {
        linhas_do_rank(r, H, size, ciclico, tmp);
        counts[r] = (int)tmp.size() * W;
        displs[r] = acc;
        acc += counts[r];
    }

    double t_com0 = MPI_Wtime();
    vector<long> buffer(rank == 0 ? (size_t)W*H : 0);
    MPI_Gatherv(local.data(), (int)local.size(), MPI_LONG,
                rank == 0 ? buffer.data() : nullptr,
                counts.data(), displs.data(), MPI_LONG, 0, MPI_COMM_WORLD);
    double t_com = MPI_Wtime() - t_com0;

    double tmax = 0, tmin = 0, tcom_max = 0;
    MPI_Reduce(&t_calc, &tmax, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&t_calc, &tmin, 1, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD);
    MPI_Reduce(&t_com, &tcom_max, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        vector<long> hist((size_t)W*H);
        for (int r = 0; r < size; r++) {
            linhas_do_rank(r, H, size, ciclico, tmp);
            for (size_t k = 0; k < tmp.size(); k++)
                memcpy(&hist[(size_t)tmp[k]*W], &buffer[displs[r] + k*W], W*sizeof(long));
        }
        long soma = 0;
        for (size_t i = 0; i < (size_t)W*H; i++) soma += hist[i];
        double t_total = MPI_Wtime() - t0;

        printf("W=%d H=%d  checksum=%ld  tempo=%.6f s\n", W, H, soma, t_total);
        printf("processos=%d decomposicao=%s t_calc_max=%.6f t_calc_min=%.6f "
               "desbalanceamento=%.2f%% t_comunicacao=%.6f\n",
               size, ciclico ? "ciclico" : "bloco", tmax, tmin,
               tmax > 0 ? 100.0 * (tmax - tmin) / tmax : 0.0, tcom_max);
    }

    MPI_Finalize();
    return 0;
}
