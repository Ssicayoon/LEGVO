   for (i = _PB_N-1; i >=0; i--) {
     DATA_TYPE aii = A[i][i];  // extract
     w = y[i];
     for (j = i+1; j < _PB_N; j++)
        w -= A[i][j] * x[j];
     x[i] = w / aii;  // use scalar, write back
  }
