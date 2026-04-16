#pragma scop
  for (i = 0; i < _PB_N; i++) {
     //j<i
     for (k = 0; k < i; k++) {
        for (j = k+1; j < i; j++) {
           A[i][j] -= A[i][k] * A[j][k];
        }
        A[i][k] /= A[k][k];
        A[i][i] -= A[i][k] * A[i][k];
     }
     A[i][i] = SQRT_FUN(A[i][i]);
  }
#pragma endscop
