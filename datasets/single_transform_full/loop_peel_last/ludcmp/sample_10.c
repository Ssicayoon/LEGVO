  for (i = 0; i < _PB_N; i++) {
     w = b[i];
     for (j = 0; j < i - 1; j++)    // peeled: last iteration j = i-1
        w -= A[i][j] * y[j];
     if (i > 0)                       // execute peeled last iteration
        w -= A[i][i-1] * y[i-1];
     y[i] = w;
  }
