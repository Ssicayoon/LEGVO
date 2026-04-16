#pragma scop
  for (i = 0; i < _PB_N; i++) {
    for (j = 0; j <= i; j++)
      C[i][j] *= beta;
    for (k = 0; k < _PB_M; k++) {
      DATA_TYPE a_ik = A[i][k];
      for (j = 0; j <= i; j++)
        C[i][j] += alpha * a_ik * A[j][k];
    }
  }
#pragma endscop
