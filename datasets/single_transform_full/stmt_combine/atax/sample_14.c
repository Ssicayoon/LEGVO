for (i = 0; i < _PB_M; i++)
    {
      for (j = 0; j < _PB_N; j++)
	tmp[i] = (j == 0 ? SCALAR_VAL(0.0) : tmp[i]) + A[i][j] * x[j];
