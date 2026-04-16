#pragma scop
  for (i = 0; i < _PB_N; i++) {
    if (_PB_M > 0) {
      for (j = 0; j <= i; j++) {
        C[i][j] *= beta;
        C[i][j] += A[j][0]*alpha*B[i][0] + B[j][0]*alpha*A[i][0];
      }
      for (k = 1; k < _PB_M; k++)
        for (j = 0; j <= i; j++)
          C[i][j] += A[j][k]*alpha*B[i][k] + B[j][k]*alpha*A[i][k];
    } else {
      for (j = 0; j <= i; j++)
        C[i][j] *= beta;
    }
  }
#pragma endscop
