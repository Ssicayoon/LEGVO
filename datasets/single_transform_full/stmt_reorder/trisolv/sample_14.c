#pragma scop
  for (i = 0; i < _PB_N; i++)
    {
      for (j = 0; j < i; j++)
        x[i] -= L[i][j] * x[j];
      x[i] = b[i] - (x[i] - SCALAR_VAL(0.0));
