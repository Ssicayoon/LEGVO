for (i = 0; i < _PB_NI; i++)
  for (j = 0; j < _PB_NJ; j++)
    for (k = 0; k < _PB_NK; ++k) {
      if (k == 0) E[i][j] = SCALAR_VAL(0.0);
      E[i][j] += A[i][k] * B[k][j];
    }
