for (i = _PB_N-1; i >=0; i--) {
     w = b[i];  // wait, it's w = y[i]
     for (j = i+1; j < _PB_N; j++)
        w -= A[i][j] * x[j];
     x[i] = w / A[i][i];
  }
