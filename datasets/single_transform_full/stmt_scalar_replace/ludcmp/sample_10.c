  for (i = 0; i < _PB_N; i++) {
     w = b[i];
     for (j = 0; j < i; j++) {
        DATA_TYPE yj = y[j];
        w -= A[i][j] * yj;
     }
     y[i] = w;
  }
