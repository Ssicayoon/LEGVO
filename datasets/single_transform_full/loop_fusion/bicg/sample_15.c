#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "bicg.h"
static void init_array (int m, int n, DATA_TYPE POLYBENCH_2D(A,N,M,n,m), DATA_TYPE POLYBENCH_1D(r,N,n), DATA_TYPE POLYBENCH_1D(p,M,m)) { int i, j; for (i = 0; i < m; i++) p[i] = (DATA_TYPE)(i % m) / m; for (i = 0; i < n; i++) { r[i] = (DATA_TYPE)(i % n) / n; for (j = 0; j < m; j++) A[i][j] = (DATA_TYPE) (i*(j+1) % n)/n; } }
static void print_array(int m, int n, DATA_TYPE POLYBENCH_1D(s,M,m), DATA_TYPE POLYBENCH_1D(q,N,n)) { int i; POLYBENCH_DUMP_START; POLYBENCH_DUMP_BEGIN("s"); for (i = 0; i < m; i++) { if (i % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n"); fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, s[i]); } POLYBENCH_DUMP_END("s"); POLYBENCH_DUMP_BEGIN("q"); for (i = 0; i < n; i++) { if (i % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n"); fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, q[i]); } POLYBENCH_DUMP_END("q"); POLYBENCH_DUMP_FINISH; }
