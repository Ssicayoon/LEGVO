  for (i = 0; i < _PB_N; i++)
    for (j = 0; j < _PB_N; j++)
      w[i] = w[i] + alpha * A[i][j] * x[j];
