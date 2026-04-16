#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "durbin.h"
static void init_array (int n, DATA_TYPE POLYBENCH_1D(r,N,n)) { int i, j; for (i = 0; i < n; i++) { r[i] = (n+1-i); } }
static void print_array(int n, DATA_TYPE POLYBENCH_1D(y,N,n)) { int i; POLYBENCH_DUMP_START; POLYBENCH_DUMP_BEGIN("y"); for (i = 0; i < n; i++) { if (i % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n"); fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, y[i]); } POLYBENCH_DUMP_END("y"); POLYBENCH_DUMP_FINISH; }
