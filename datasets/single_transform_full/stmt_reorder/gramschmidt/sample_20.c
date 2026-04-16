static
void kernel_gramschmidt(int m, int n,
			DATA_TYPE POLYBENCH_2D(A,M,N,m,n),
			DATA_TYPE POLYBENCH_2D(R,N,N,n,n),
			DATA_TYPE POLYBENCH_2D(Q,M,N,m,n))
{
  int i, j, k;

  DATA_TYPE nrm;

#pragma scop
  for (k = 0; k < _PB_N; k++)
    {
      nrm = SCALAR_VAL(0.0);
      for (i = 0; i < _PB_M; i++)
        nrm += A[i][k] * A[i][k];
      R[k][k] = SQRT_FUN(nrm);
      for (j = k + 1; j < _PB_N; j++)
	{
	  R[k][j] = SCALAR_VAL(0.0);
	  for (i = 0; i < _PB_M; i++)
	    Q[i][k] = A[i][k] / R[k][k];
	  for (i = 0; i < _PB_M; i++)
	    R[k][j] += Q[i][k] * A[i][j];
	  for (i = 0; i < _PB_M; i++)
	    A[i][j] = A[i][j] - Q[i][k] * R[k][j];
	}
    }
#pragma endscop
