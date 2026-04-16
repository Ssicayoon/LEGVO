#pragma scop
  for (i = 0; i < _PB_N; i++) {
    for (j = 0; j+(-1) < i; j++)
      C[i][j] *= beta;
    for (k = 0; k < _PB_M; k++) {
      for (j = 0; j <= i; j++)
        C[i][j] += alpha * A[i][k] * A[j][k];
    }
  }
#pragma endscop
