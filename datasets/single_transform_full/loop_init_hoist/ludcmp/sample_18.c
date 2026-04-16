  for (i = 0; i < _PB_N; i++) {
     w = 0;
     w += b[i];
     for (j = 0; j < i; j++)
        w -= A[i][j] * y[j];
     y[i] = w;
  }
