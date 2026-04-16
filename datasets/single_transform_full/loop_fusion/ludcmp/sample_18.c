#pragma scop
  for (i = 0; i < _PB_N; i++) {
    for (j = 0; j < _PB_N; j++) {
      w = A[i][j];
      if (j < i) {
        for (k = 0; k < j; k++) {
          w -= A[i][k] * A[k][j];
        }
        A[i][j] = w / A[j][j];
      } else {
        for (k = 0; k < i; k++) {
          w -= A[i][k] * A[k][j];
        }
        A[i][j] = w;
      }
    }
  }

  for (i = 0; i < _PB_N; i++) {
     w = b[i];
     for (j = 0; j < i; j++)
        w -= A[i][j] * y[j];
     y[i] = w;
  }

   for (i = _PB_N-1; i >=0; i--) {
     w = y[i];
     for (j = i+1; j < _PB_N; j++)
        w -= A[i][j] * x[j];
     x[i] = w / A[i][i];
  }
#pragma endscop
