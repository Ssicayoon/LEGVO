#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "atax.h"

static void init_array (int m, int n, DATA_TYPE POLYBENCH_2D(A,M,N,m,n), DATA_TYPE POLYBENCH_1D(x,N,n)) { int i, j; DATA_TYPE fn; fn = (DATA_TYPE)n; for (i = 0; i < n; i++) x[i] = 1 + (i / fn); for (i = 0; i < m; i++) for (j = 0; j < n; j++) A[i][j] = (DATA_TYPE) ((i+j) % n) / (5*m); }
static void print_array(int n, DATA_TYPE POLYBENCH_1D(y,N,n)) { int i; POLYBENCH_DUMP_START; POLYBENCH_DUMP_BEGIN("y"); for (i = 0; i < n; i++) { if (i % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n"); fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, y[i]); } POLYBENCH_DUMP_END("y"); POLYBENCH_DUMP_FINISH; }
