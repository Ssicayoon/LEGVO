#pragma scop
  for (i = 0; i < _PB_N; i++) {
    for (j = 0; j <= i; j++)
      C[i][j] *= beta;
    for (j = 0; j <= i; j++) {
      DATA_TYPE tmp = C[i][j];
      for (k = 0; k < _PB_M; k++) {
        tmp += alpha * A[i][k] * A[j][k];
      }
      C[i][j] = tmp;
    }
  }
#pragma endscop
