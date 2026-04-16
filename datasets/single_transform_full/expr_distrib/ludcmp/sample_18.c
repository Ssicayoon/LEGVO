   for (i = _PB_N-1; i >=0; i--) {
     x[i] = y[i] / A[i][i];
     for (j = i+1; j < _PB_N; j++)
        x[i] -= A[i][j] * x[j] / A[i][i];
  }
