#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "doitgen.h"

static void init_array(int nr, int nq, int np, DATA_TYPE POLYBENCH_3D(A,NR,NQ,NP,nr,nq,np), DATA_TYPE POLYBENCH_2D(C4,NP,NP,np,np)) { int i, j, k; for (i = 0; i < nr; i++) for (j = 0; j < nq; j++) for (k = 0; k < np; k++) A[i][j][k] = (DATA_TYPE) ((i*j + k)%np) / np; for (i = 0; i < np; i++) for (j = 0; j < np; j++) C4[i][j] = (DATA_TYPE) (i*j % np) / np; }
static void print_array(int nr, int nq, int np, DATA_TYPE POLYBENCH_3D(A,NR,NQ,NP,nr,nq,np)) { int i, j, k; POLYBENCH_DUMP_START; POLYBENCH_DUMP_BEGIN("A"); for (i = 0; i < nr; i++) for (j = 0; j < nq; j++) for (k = 0; k < np; k++) { if ((i*nq*np+j*np+k) % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n"); fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, A[i][j][k]); } POLYBENCH_DUMP_END("A"); POLYBENCH_DUMP_FINISH; }
