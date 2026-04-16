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
    for (j = 0; j+(-1) < i; j++)
      C[i][j] *= beta;
