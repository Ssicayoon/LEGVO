static
void kernel_cholesky(int n,
		     DATA_TYPE POLYBENCH_2D(A,N,N,n,n))
{
  int i, j, k;
  DATA_TYPE temp;

#pragma scop
  for (i = 0; i < _PB_N; i++) {
     for (j = 0; j < i; j++) {
        for (k = 0; k < j; k++) {
           A[i][j] -= A[i][k] * A[j][k];
        }
        A[i][j] /= A[j][j];
     }
     temp = 0;
     for (k = 0; k < i; k++) {
        temp += A[i][k] * A[i][k];
     }
     A[i][i] -= temp;
     A[i][i] = SQRT_FUN(A[i][i]);
  }
#pragma endscop

}
