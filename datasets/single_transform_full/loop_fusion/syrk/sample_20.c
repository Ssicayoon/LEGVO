static
void kernel_syrk(int n, int m,
		 DATA_TYPE alpha,
		 DATA_TYPE beta,
		 DATA_TYPE POLYBENCH_2D(C,N,N,n,n),
		 DATA_TYPE POLYBENCH_2D(A,N,M,n,m))
{
  int i, j, k;

#pragma scop
  for (i = 0; i < _PB_N; i++) {
    for (j = 0; j <= i; j++) {
      C[i][j] *= beta;
      C[i][j] += alpha * A[i][0] * A[j][0];
    }
    for (k = 1; k < _PB_M; k++) {
      for (j = 0; j <= i; j++)
        C[i][j] += alpha * A[i][k] * A[j][k];
    }
  }
#pragma endscop

}
