for (i = 0; i < _PB_M; i++)
  for (j = k + 1; j < _PB_N; j++)
    R[k][j] += Q[i][k] * A[i][j];
