#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "gramschmidt.h"
static void init_array(int m, int n, DATA_TYPE POLYBENCH_2D(A,M,N,m,n), DATA_TYPE POLYBENCH_2D(R,N,N,n,n), DATA_TYPE POLYBENCH_2D(Q,M,N,m,n)) { int i, j; for (i = 0; i < m; i++) for (j = 0; j < n; j++) { A[i][j] = (((DATA_TYPE) ((i*j) % m) / m )*100) + 10; Q[i][j] = 0.0; } for (i = 0; i < n; i++) for (j = 0; j < n; j++) R[i][j] = 0.0; }
