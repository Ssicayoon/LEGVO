for (i = 0; i < _PB_M; i++)
  for (j = 0; j < _PB_N; j++)
    y[j] = y[j] + A[i][j] * tmp[i];
