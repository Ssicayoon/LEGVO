  for (i = 0; i < _PB_N; i++) {
    // merged: beta scaling + k=0 update in one j loop
    for (j = 0; j <= i; j++) {
      C[i][j] *= beta;
      C[i][j] += alpha * A[i][0] * A[j][0];
    }
    for (k = 1; k < _PB_M; k++) {
      for (j = 0; j <= i; j++)
        C[i][j] += alpha * A[i][k] * A[j][k];
    }
  }
