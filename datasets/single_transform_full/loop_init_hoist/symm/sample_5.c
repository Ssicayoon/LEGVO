static
void kernel_symm(int m, int n,
		 DATA_TYPE alpha,
		 DATA_TYPE beta,
		 DATA_TYPE POLYBENCH_2D(C,M,N,m,n),
		 DATA_TYPE POLYBENCH_2D(A,M,M,m,m),
		 DATA_TYPE POLYBENCH_2D(B,M,N,m,n))
{
  int i, j, k;
  DATA_TYPE temp2;

#pragma scop
   temp2 = 0;
   for (i = 0; i < _PB_M; i++)
      for (j = 0; j < _PB_N; j++ )
      {
        temp2 = 0;
        for (k = 0; k < i; k++) {
           C[k][j] += alpha*B[i][j] * A[i][k];
           temp2 += B[k][j] * A[i][k];
        }
        C[i][j] = beta * C[i][j] + alpha*B[i][j] * A[i][i] + alpha * temp2;
     }
#pragma endscop

}
