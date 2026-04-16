#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "lu.h"

static void init_array (int n, DATA_TYPE POLYBENCH_2D(A,N,N,n,n)) { int i, j; for (i = 0; i < n; i++) { for (j = 0; j <= i; j++) A[i][j] = (DATA_TYPE)(-j % n) / n + 1; for (j = i+1; j < n; j++) { A[i][j] = 0; } A[i][i] = 1; } int r,s,t; POLYBENCH_2D_ARRAY_DECL(B, DATA_TYPE, N, N, n, n); for (r = 0; r < n; ++r) for (s = 0; s < n; ++s) (POLYBENCH_ARRAY(B))[r][s] = 0; for (t = 0; t < n; ++t) for (r = 0; r < n; ++r) for (s = 0; s < n; ++s) (POLYBENCH_ARRAY(B))[r][s] += A[r][t] * A[s][t]; for (r = 0; r < n; ++r) for (s = 0; s < n; ++s) A[r][s] = (POLYBENCH_ARRAY(B))[r][s]; POLYBENCH_FREE_ARRAY(B); }
static void print_array(int n, DATA_TYPE POLYBENCH_2D(A,N,N,n,n)) { int i, j; POLYBENCH_DUMP_START; POLYBENCH_DUMP_BEGIN("A"); for (i = 0; i < n; i++) for (j = 0; j < n; j++) { if ((i * n + j) % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n"); fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, A[i][j]); } POLYBENCH_DUMP_END("A"); POLYBENCH_DUMP_FINISH; }
