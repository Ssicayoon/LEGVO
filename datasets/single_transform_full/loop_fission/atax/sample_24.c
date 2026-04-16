for (i = 0; i < _PB_M; i++)
  {
    tmp[i] = SCALAR_VAL(0.0);           // stmt 1
    for (j = 0; j < _PB_N; j++)
      tmp[i] = tmp[i] + A[i][j] * x[j]; // stmt 2 (depends on stmt 1)
    for (j = 0; j < _PB_N; j++)
      y[j] = y[j] + A[i][j] * tmp[i];   // stmt 3 (depends on stmt 2)
  }
