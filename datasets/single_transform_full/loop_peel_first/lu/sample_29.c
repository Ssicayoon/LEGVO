static
void kernel_lu(int n,
	       DATA_TYPE POLYBENCH_2D(A,N,N,n,n))
{
  int i, j, k;

#pragma scop
  /* Peeled first iteration: i = 0 */
  for (j = 0; j < 0; j++) {
     for (k = 0; k < j; k++) {
        A[0][j] -= A[0][k] * A[k][j];
     }
      A[0][j] /= A[j][j];
  }
  for (j = 0; j < _PB_N; j++) {
     for (k = 0; k < 0; k++) {
        A[0][j] -= A[0][k] * A[k][j];
     }
  }
  /* Remaining iterations: i = 1 .. _PB_N-1 */
  for (i = 1; i < _PB_N; i++) {
    for (j = 0; j <i; j++) {
       for (k = 0; k < j; k++) {
          A[i][j] -= A[i][k] * A[k][j];
       }
        A[i][j] /= A[j][j];
    }
   for (j = i; j < _PB_N; j++) {
       for (k = 0; k < i; k++) {
          A[i][j] -= A[i][k] * A[k][j];
       }
    }
  }
#pragma endscop
}
