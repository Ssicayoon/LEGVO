#pragma scop
  for (i = 0; i < _PB_NI; i++) {
    for (j = 0; j < _PB_NJ; j++)
	C[i][j] *= beta;
    for (k = 0; k < _PB_NK; k++) {
       for (j = 0; j < _PB_NJ; j++)
	  C[i][j] += A[i][k] * (alpha * B[k][j]);
    }
  }
#pragma endscop
