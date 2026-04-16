  for (i = 0; i < _PB_N; i++) {
     y[i] = b[i];
     for (j = 0; j < i; j++)
        y[i] -= A[i][j] * y[j];
  }
