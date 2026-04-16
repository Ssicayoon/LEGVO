  for (i = 0; i < _PB_N; i++) {
     DATA_TYPE bi = b[i];
     w = bi;
     for (j = 0; j < i; j++)
        w -= A[i][j] * y[j];
     y[i] = w;
  }
