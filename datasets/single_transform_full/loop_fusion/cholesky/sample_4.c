#pragma scop
  for (i = 0; i < _PB_N; i++) {
     //j<i
     for (j = 0; j < i; j++) {
        for (k = 0; k < j; k++) {
           A[i][j] -= A[i][k] * A[j][k];
        }
        A[i][j] /= A[j][j];
        A[i][i] -= A[i][j] * A[i][j];
     }
     A[i][i] = SQRT_FUN(A[i][i]);
  }
#pragma endscop
