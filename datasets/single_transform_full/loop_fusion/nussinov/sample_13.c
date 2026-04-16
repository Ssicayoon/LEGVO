#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "nussinov.h"

typedef char base;

#define match(b1, b2) (((b1)+(b2)) == 3 ? 1 : 0)
#define max_score(s1, s2) ((s1 >= s2) ? s1 : s2)

static void init_array (int n, base POLYBENCH_1D(seq,N,n), DATA_TYPE POLYBENCH_2D(table,N,N,n,n)) { int i, j; for (i=0; i <n; i++) { seq[i] = (base)((i+1)%4); } for (i=0; i <n; i++) for (j=0; j <n; j++) table[i][j] = 0; }
static void print_array(int n, DATA_TYPE POLYBENCH_2D(table,N,N,n,n)) { int i, j; int t = 0; POLYBENCH_DUMP_START; POLYBENCH_DUMP_BEGIN("table"); for (i = 0; i < n; i++) { for (j = i; j < n; j++) { if (t % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n"); fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, table[i][j]); t++; } } POLYBENCH_DUMP_END("table"); POLYBENCH_DUMP_FINISH; }
