for (j = 0; j < _PB_NJ; j++)
  {
    tmp[i][j] = SCALAR_VAL(0.0);
    for (k = 0; k < _PB_NK; ++k)
      tmp[i][j] += alpha * A[i][k] * B[k][j];
  }
