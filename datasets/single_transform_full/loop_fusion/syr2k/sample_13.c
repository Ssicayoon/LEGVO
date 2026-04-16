Looking at the kernel, I need to find two adjacent same-bound loops to merge.

Inside the outer `i` loop, there are two adjacent loops:
1. `for (j = 0; j <= i; j++)` — scales C[i][j] by beta
2. `for (k = 0; k < _PB_M; k++) for (j = 0; j <= i; j++)` — updates C[i][j]

These don't have the same bound directly. But I can look at a different location.

Actually, looking more carefully: the two inner constructs both involve `j` going from `0` to `i`, but the second one has an outer `k` loop. These aren't directly mergeable as-is.

Wait — I should consider merging the `j` loop inside the `k` loop with... no.

The transformation I can apply: merge the first `for (j = 0; j <= i; j++)` with a restructured version. But the second loop has an extra `k` dimension.

Alternative: I can merge at the outer level if there were two adjacent `i` loops — but there's only one.

The valid merge here is: move the beta scaling into the k-loop by handling it on first iteration (not semantically simple) OR restructure so the `j` loop for beta scaling is merged with the `j` loop inside `k=0` iteration. That changes semantics.

The cleanest valid merge: introduce a fused `j` loop that does both beta scaling AND the k-accumulation, by separating the k loop — but they don't have the same bounds.

Actually, the two adjacent loops with the same bound `j: 0..i` are: the first `for j` loop and the innermost `for j` loop (when k is fixed). I can merge them only if I restructure the k loop.

The correct approach: merge the beta-scaling j-loop with the first iteration (k=0) of the inner j-loop, peeling k=0.

```c
/**
 * ... (header unchanged)
 */
/* syr2k.c: this file is part of PolyBench/C */

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>

#include <polybench.h>
#include "syr2k.h"

static
void init_array(int n, int m,
		DATA_TYPE *alpha,
		DATA_TYPE *beta,
		DATA_TYPE POLYBENCH_2D(C,N,N,n,n),
		DATA_TYPE POLYBENCH_2D(A,N,M,n,m),
		DATA_TYPE POLYBENCH_2D(B,N,M,n,m))
{
  int i, j;
  *alpha = 1.5;
  *beta = 1.2;
  for (i = 0; i < n; i++)
    for (j = 0; j < m; j++) {
      A[i][j] = (DATA_TYPE) ((i*j+1)%n) / n;
      B[i][j] = (DATA_TYPE) ((i*j+2)%m) / m;
    }
  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++) {
      C[i][j] = (DATA_TYPE) ((i*j+3)%n) / m;
    }
}

static
void print_array(int n,
		 DATA_TYPE POLYBENCH_2D(C,N,N,n,n))
{
  int i, j;
  POLYBENCH_DUMP_START;
  POLYBENCH_DUMP_BEGIN("C");
  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++) {
	if ((i * n + j) % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n");
	fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, C[i][j]);
    }
  POLYBENCH_DUMP_END("C");
  POLYBENCH_DUMP_FINISH;
}

static
void kernel_syr2k(int n, int m,
		  DATA_TYPE alpha,
		  DATA_TYPE beta,
		  DATA_TYPE POLYBENCH_2D(C,N,N,n,n),
		  DATA_TYPE POLYBENCH_2D(A,N,M,n,m),
		  DATA_TYPE POLYBENCH_2D(B,N,M,n,m))
{
  int i, j, k;

#pragma scop
  for (i = 0; i < _PB_N; i++) {
    for (j = 0; j <= i; j++) {
      C[i][j] *= beta;
      C[i][j] += A[j][0]*alpha*B[i][0] + B[j][0]*alpha*A[i][0];
    }
    for (k = 1; k < _PB_M; k++)
      for (j = 0; j <= i; j++)
	{
	  C[i][j] += A[j][k]*alpha*B[i][k] + B[j][k]*alpha*A[i][k];
	}
  }
#pragma endscop

}

int main(int argc, char** argv)
{
  int n = N;
  int m = M;
  DATA_TYPE alpha;
  DATA_TYPE beta;
  POLYBENCH_2D_ARRAY_DECL(C,DATA_TYPE,N,N,n,n);
  POLYBENCH_2D_ARRAY_DECL(A,DATA_TYPE,N,M,n,m);
  POLYBENCH_2D_ARRAY_DECL(B,DATA_TYPE,N,M,n,m);

  init_array (n, m, &alpha, &beta,
	      POLYBENCH_ARRAY(C),
	      POLYBENCH_ARRAY(A),
	      POLYBENCH_ARRAY(B));

  polybench_start_instruments;

  kernel_syr2k (n, m,
		alpha, beta,
		POLYBENCH_ARRAY(C),
		POLYBENCH_ARRAY(A),
		POLYBENCH_ARRAY(B));

  polybench_stop_instruments;
  polybench_print_instruments;

  polybench_prevent_dce(print_array(n, POLYBENCH_ARRAY(C)));

  POLYBENCH_FREE_ARRAY(C);
  POLYBENCH_FREE_ARRAY(A);
  POLYBENCH_FREE_ARRAY(B);

  return 0;
}