#pragma scop
   for (i = 0; i < _PB_M; i++)
      for (j = 0; j < _PB_N; j++ )
      {
        C[i][j] = beta * C[i][j] + alpha*B[i][j] * A[i][i];
        for (k = 0; k < i; k++) {
           C[k][j] += alpha*B[i][j] * A[i][k];
           C[i][j] += alpha * B[k][j] * A[i][k];
        }
     }
#pragma endscop
