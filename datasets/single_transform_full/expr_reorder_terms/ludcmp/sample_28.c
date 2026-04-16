   for (i = _PB_N-1; i >=0; i--) {
     w = y[i];
     for (j = 1+i; j < _PB_N; j++)
        w -= A[i][j] * x[j];
     x[i] = w / A[i][i];
  }
