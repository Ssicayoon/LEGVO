#pragma scop
  for (i = 0; i < _PB_M; i++)
     for (k = i+1; k < _PB_M; k++)
        for (j = 0; j < _PB_N; j++)
           B[i][j] += A[k][i] * B[k][j];
  for (i = 0; i < _PB_M; i++)
     for (j = 0; j < _PB_N; j++)
        B[i][j] = alpha * B[i][j];
#pragma endscop
