   for (i = _PB_N-1; i >=0; i--) {
     w = y[i];
     for (j = i+1; j < _PB_N; j++)
        w -= A[i][j] * x[j];
     DATA_TYPE aii = A[i][i];   // extract
     x[i] = w / aii;            // write back
  }
