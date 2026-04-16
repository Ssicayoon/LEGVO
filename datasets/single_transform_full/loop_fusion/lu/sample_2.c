#pragma scop
  for (i = 0; i < _PB_N; i++) {
    for (j = 0; j < _PB_N; j++) {
      if (j < i) {
        for (k = 0; k < j; k++) {
           A[i][j] -= A[i][k] * A[k][j];
        }
        A[i][j] /= A[j][j];
      } else {
        for (k = 0; k < i; k++) {
           A[i][j] -= A[i][k] * A[k][j];
        }
      }
    }
  }
#pragma endscop
