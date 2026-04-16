#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "3mm.h"

static void init_array(int ni, int nj, int nk, int nl, int nm, DATA_TYPE POLYBENCH_2D(A,NI,NK,ni,nk), DATA_TYPE POLYBENCH_2D(B,NK,NJ,nk,nj), DATA_TYPE POLYBENCH_2D(C,NJ,NM,nj,nm), DATA_TYPE POLYBENCH_2D(D,NM,NL,nm,nl)) { int i, j; for (i = 0; i < ni; i++) for (j = 0; j < nk; j++) A[i][j] = (DATA_TYPE) ((i*j+1) % ni) / (5*ni); for (i = 0; i < nk; i++) for (j = 0; j < nj; j++) B[i][j] = (DATA_TYPE) ((i*(j+1)+2) % nj) / (5*nj); for (i = 0; i < nj; i++) for (j = 0; j < nm; j++) C[i][j] = (DATA_TYPE) (i*(j+3) % nl) / (5*nl); for (i = 0; i < nm; i++) for (j = 0; j < nl; j++) D[i][j] = (DATA_TYPE) ((i*(j+2)+2) % nk) / (5*nk); }
static void print_array(int ni, int nl, DATA_TYPE POLYBENCH_2D(G,NI,NL,ni,nl)) { int i, j; POLYBENCH_DUMP_START; POLYBENCH_DUMP_BEGIN("G"); for (i = 0; i < ni; i++) for (j = 0; j < nl; j++) { if ((i * ni + j) % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n"); fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, G[i][j]); } POLYBENCH_DUMP_END("G"); POLYBENCH_DUMP_FINISH; }
