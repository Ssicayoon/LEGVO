static
void kernel_bicg(int m, int n,
		 DATA_TYPE POLYBENCH_2D(A,N,M,n,m),
		 DATA_TYPE POLYBENCH_1D(s,M,m),
		 DATA_TYPE POLYBENCH_1D(q,N,n),
		 DATA_TYPE POLYBENCH_1D(p,M,m),
		 DATA_TYPE POLYBENCH_1D(r,N,n))
{
  int i, j;

#pragma scop
  for (i = 0; i < _PB_M; i++)
    s[i] = 0;
  for (i = 0; i < _PB_N; i++)
    {
      q[i] = A[i][0] * p[0];
      for (j = 1; j < _PB_M; j++)
	{
	  s[j] = s[j] + r[i] * A[i][j];
	  q[i] = q[i] + A[i][j] * p[j];
	}
      s[0] = s[0] + r[i] * A[i][0];
    }
#pragma endscop

}
