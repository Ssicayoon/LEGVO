#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "heat-3d.h"

static void init_array (int n, DATA_TYPE POLYBENCH_3D(A,N,N,N,n,n,n), DATA_TYPE POLYBENCH_3D(B,N,N,N,n,n,n)) {
  int i, j, k;
  for (i = 0; i < n; i++) for (j = 0; j < n; j++) for (k = 0; k < n; k++) A[i][j][k] = B[i][j][k] = (DATA_TYPE) (i + j + (n-k))* 10 / (n);
}

static void print_array(int n, DATA_TYPE POLYBENCH_3D(A,N,N,N,n,n,n)) {
  int i, j, k;
  POLYBENCH_DUMP_START; POLYBENCH_DUMP_BEGIN("A");
  for (i = 0; i < n; i++) for (j = 0; j < n; j++) for (k = 0; k < n; k++) { if ((i * n * n + j * n + k) % 20 == 0) fprintf(POLYBENCH_DUMP_TARGET, "\n"); fprintf(POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, A[i][j][k]); }
  POLYBENCH_DUMP_END("A"); POLYBENCH_DUMP_FINISH;
}
