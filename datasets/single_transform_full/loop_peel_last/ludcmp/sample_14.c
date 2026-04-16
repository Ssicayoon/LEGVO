  for (i = 0; i < _PB_N - 1; i++) {
     w = b[i];
     for (j = 0; j < i; j++)
        w -= A[i][j] * y[j];
     y[i] = w;
  }
  /* Peeled last iteration: i = _PB_N - 1 */
  {
     i = _PB_N - 1;
     w = b[i];
     for (j = 0; j < i; j++)
        w -= A[i][j] * y[j];
     y[i] = w;
  }
