Looking at the kernel, I need to find two adjacent same-bound loops to merge.

Inside the outer `i` loop, I have:
1. `for (j = 0; j <= i; j++)` — scales C[i][j] by beta
2. `for (k = 0; k < _PB_M; k++)` with inner `for (j = 0; j <= i; j++)` — updates C[i][j]

These two aren't directly mergeable as-is due to the k loop in between.

However, I can look at the `k` loop structure. The inner `j` loop inside `k` runs `j <= i`, same as the first `j` loop. But they're not adjacent at the same level.

Actually, the best candidate is: the `j` loop (beta scaling) and the `k` loop are adjacent under `i`, but different bounds. 

Wait — I can merge the two `j` loops if I restructure. The first `j` loop and the `j` loop inside `k=0` iteration... but that changes semantics.

The cleanest merge: move the beta scaling into the k-loop by handling it at k=0, but that changes structure significantly.

**Variant 10 approach**: Merge the outer `i` loop with itself isn't possible. Let me reconsider — merge the `j`-loop (beta) with the inner `j`-loop by pulling it into the k-loop when k==0, but instead let me just merge the two adjacent `j` loops that appear when we consider that after rewriting the k-loop first iteration... 

Actually the simplest: the two `j` loops (beta scaling `j<=i` and the update `j<=i` inside k) can be merged if we fold the beta scaling into the k=0 case. But semantically we need beta applied once.

The real mergeable pair at a **different location**: within a fixed `i` and `k`, there's only one `j` loop. Let me merge the `i`-level: the beta `j`-loop and the k-update block are adjacent under `i`. They have different bounds so can't merge directly.

**Solution**: Merge the two adjacent `j`-loops by combining them — apply beta in the same loop as the k=0 update, separating into one j-loop with both operations when k==0:

```c
/**
 * This version is stamped on May 10, 2016
 *
 * Contact:
 *   Louis-Noel Pouchet <pouchet.ohio-state.edu>
 *   Tomofumi Yuki <tomofumi.yuki.fr>
 *
 * Web address: http://polybench.sourceforge.net
 */
/* syrk.c: this file is part of PolyBench/C */

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>

/* Include polybench common header. */
#include <polybench.h>

/* Include benchmark-specific header. */
#include "syrk.h"


/* Array initialization. */
static
void init_array(int n, int m,
		DATA_TYPE *alpha,
		DATA_TYPE *beta,
		DATA_TYPE POLYBENCH_2D(C,N,N,n,n),
		DATA_TYPE POLYBENCH_2D(A,N,M,n,m))
{
  int i, j;

  *alpha = 1.5;
  *beta = 1.2;
  for (i = 0; i < n; i++)
    for (j = 0; j < m; j++)
      A[i][j] = (DATA_TYPE) ((i*j+1)%n) / n;
  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++)
      C[i][j] = (DATA_TYPE) ((i*j+2)%m) / m;
}


/* DCE code. Must scan the entire live-out data.
   Can be used also to check the correctness of the output. */
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


/* Main computational kernel. The whole function will be timed,
   including the call and return. */
static
void kernel_syrk(int n, int m,
		 DATA_TYPE alpha,
		 DATA_TYPE beta,
		 DATA_TYPE POLYBENCH_2D(C,N,N,n,n),
		 DATA_TYPE POLYBENCH_2D(A,N,M,n,m))
{
  int i, j, k;

//BLAS PARAMS
//TRANS = 'N'
//UPLO  = 'L'
// =>  Form  C := alpha*A*A**T + beta*C.
//A is NxM
//C is NxN
#pragma scop
  for (i = 0; i < _PB_N; i++) {
    for (k = 0; k < _PB_M; k++) {
      for (j = 0; j <= i; j++) {
        if (k == 0) C[i][j] *= beta;
        C[i][j] += alpha * A[i][k] * A[j][k];
      }
    }
  }
#pragma endscop

}


int main(int argc, char** argv)
{
  /* Retrieve problem size. */
  int n = N;
  int m = M;

  /* Variable declaration/allocation. */
  DATA_TYPE alpha;
  DATA_TYPE beta;
  POLYBENCH_2D_ARRAY_DECL(C,DATA_TYPE,N,N,n,n);
  POLYBENCH_2D_ARRAY_DECL(A,DATA_TYPE,N,M,n,m);

  /* Initialize array(s). */
  init_array (n, m, &alpha, &beta, POLYBENCH_ARRAY(C), POLYBENCH_ARRAY(A));

  /* Start timer. */
  polybench_start_instruments;

  /* Run kernel. */
  kernel_syrk (n, m, alpha, beta, POLYBENCH_ARRAY(C), POLYBENCH_ARRAY(A));

  /* Stop and print timer. */
  polybench_stop_instruments;
  polybench_print_instruments;

  /* Prevent dead-code elimination. All live-out data must be printed
     by the function call in argument. */
  polybench_prevent_dce(print_array(n, POLYBENCH_ARRAY(C)));

  /* Be clean. */
  POLYBENCH_FREE_ARRAY(C);
  POLYBENCH_FREE_ARRAY(A);

  return 0;
}