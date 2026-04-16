   for (i = _PB_N-1; i >=0; i--) {
     w = y[i];
     for (j = i+1; j < _PB_N; j++) {
        DATA_TYPE xj = x[j];
        w -= A[i][j] * xj;
     }
     x[i] = w / A[i][i];
  }
