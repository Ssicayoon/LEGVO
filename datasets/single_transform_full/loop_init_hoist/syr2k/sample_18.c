static
void kernel_syr2k(int n, int m,
		  DATA_TYPE alpha,
		  DATA_TYPE beta,
		  DATA_TYPE POLYBENCH_2D(C,N,N,n,n),
		  DATA_TYPE POLYBENCH_2D(A,N,M,n,m),
		  DATA_TYPE POLYBENCH_2D(B,N,M,n,m))
{
  int i, j, k;

//BLAS PARAMS
//UPLO  = 'L'
//TRANS = 'N'
//A is NxM
//B is NxM
//C is NxN
#pragma scop
  for (i = 0; i < _PB_N; i++) {
    for (j = 0; j <= i; j++)
      C[i][j] *= beta;
    for (j = 0; j <= i; j++) {
      DATA_TYPE tmp = 0;
      for (k = 0; k < _PB_M; k++)
        tmp += A[j][k]*alpha*B[i][k] + B[j][k]*alpha*A[i][k];
      C[i][j] += tmp;
    }
  }
#pragma endscop

}
