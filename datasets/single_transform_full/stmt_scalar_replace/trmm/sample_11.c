#pragma scop
  for (i = 0; i < _PB_M; i++)
     for (j = 0; j < _PB_N; j++) {
        DATA_TYPE bij = B[i][j];
        for (k = i+1; k < _PB_M; k++)
           bij += A[k][i] * B[k][j];
        B[i][j] = alpha * bij;
     }
#pragma endscop
