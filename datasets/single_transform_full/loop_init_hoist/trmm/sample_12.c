for (i = 0; i < _PB_M; i++)
   for (j = 0; j < _PB_N; j++) {
      DATA_TYPE tmp = 0;
      for (k = i+1; k < _PB_M; k++)
         tmp += A[k][i] * B[k][j];
      B[i][j] = alpha * (B[i][j] + tmp);
   }
