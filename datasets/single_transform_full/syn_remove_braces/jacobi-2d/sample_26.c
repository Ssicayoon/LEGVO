#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "jacobi-2d.h"
static void init_array (int n, DATA_TYPE POLYBENCH_2D(A,N,N,n,n), DATA_TYPE POLYBENCH_2D(B,N,N,n,n)) { int i, j; for (i = 0; i < n; i++) for (j = 0; j < n; j++) { A[i][j] = ((DATA_TYPE) i*(j+2) + 2) / n; B[i][j] = ((DATA_TYPE) i*(j+3) + 3) / n; } }
