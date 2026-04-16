#pragma scop
  for (i = 0; i < _PB_NI; i++) {
    for (j = 0; j < _PB_NJ; j++)
      C[i][j] *= beta;
  }
  for (i = 0; i < _PB_NI; i++) {
    for (k = 0; k < _PB_NK; k++) {
       for (j = 0; j < _PB_NJ; j++)
	  C[i][j] += alpha * A[i][k] * B[k][j];
    }
  }
#pragma endscop
