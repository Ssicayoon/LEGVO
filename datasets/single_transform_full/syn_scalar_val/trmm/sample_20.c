#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "trmm.h"
static void init_array(int m, int n, DATA_TYPE *alpha, DATA_TYPE POLYBENCH_2D(A,M,M,m,m), DATA_TYPE POLYBENCH_2D(B,M,N,m,n)) { int i, j; *alpha = 1.5; for (i = 0; i < m; i++) { for (j = 0; j < i; j++) { A[i][j] = (DATA_TYPE)((i+j) % m)/m; } A[i][i] = 1.0; for (j = 0; j < n; j++) { B[i][j] = (DATA_TYPE)((n+(i-j)) % n)/n; } } }
