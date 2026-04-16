#pragma scop
  for (i = 0; i < _PB_NI; i++) {
    for (j = 0; j < _PB_NJ; j++)
	C[i][j] *= beta;
    for (j = 0; j < _PB_NJ; j++) {
      DATA_TYPE cij = C[i][j];
      for (k = 0; k < _PB_NK; k++) {
        cij += alpha * A[i][k] * B[k][j];
      }
      C[i][j] = cij;
    }
  }
#pragma endscop
