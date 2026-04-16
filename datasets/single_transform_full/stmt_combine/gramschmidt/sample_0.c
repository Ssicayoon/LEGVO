#pragma scop
  for (k = 0; k < _PB_N; k++)
    {
      R[k][k] = SCALAR_VAL(0.0);
      for (i = 0; i < _PB_M; i++)
        R[k][k] += A[i][k] * A[i][k];
      R[k][k] = SQRT_FUN(R[k][k]);
      for (i = 0; i < _PB_M; i++)
        Q[i][k] = A[i][k] / R[k][k];
      for (j = k + 1; j < _PB_N; j++)
	{
	  R[k][j] = SCALAR_VAL(0.0);
	  for (i = 0; i < _PB_M; i++)
	    R[k][j] += Q[i][k] * A[i][j];
	  for (i = 0; i < _PB_M; i++)
	    A[i][j] = A[i][j] - Q[i][k] * R[k][j];
	}
    }
#pragma endscop
