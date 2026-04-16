static
void kernel_trmm(int m, int n,
		 DATA_TYPE alpha,
		 DATA_TYPE POLYBENCH_2D(A,M,M,m,m),
		 DATA_TYPE POLYBENCH_2D(B,M,N,m,n))
{
  int i, j, k;

#pragma scop
  for (i = 0; i < _PB_M; i++)
     for (j = 0; j < _PB_N; j++) {
        DATA_TYPE temp = 0;
        for (k = i+1; k < _PB_M; k++)
           temp += A[k][i] * B[k][j];
        B[i][j] = alpha * (B[i][j] + temp);
     }
#pragma endscop
}
