static
void kernel_bicg(int m, int n,
		 DATA_TYPE POLYBENCH_2D(A,N,M,n,m),
		 DATA_TYPE POLYBENCH_1D(s,M,m),
		 DATA_TYPE POLYBENCH_1D(q,N,n),
		 DATA_TYPE POLYBENCH_1D(p,M,m),
		 DATA_TYPE POLYBENCH_1D(r,N,n))
{
  int i, j, ii;

#pragma scop
  for (i = 0; i < _PB_M; i++)
    s[i] = 0;
  for (ii = 0; ii < _PB_N; ii++)
    {
      q[ii] = SCALAR_VAL(0.0);
      for (j = 0; j < _PB_M; j++)
	{
	  s[j] = s[j] + r[ii] * A[ii][j];
	  q[ii] = q[ii] + A[ii][j] * p[j];
	}
    }
#pragma endscop

}
