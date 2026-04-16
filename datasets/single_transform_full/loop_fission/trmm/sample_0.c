for (i = 0; i < _PB_M; i++)
   for (j = 0; j < _PB_N; j++)
      for (k = i+1; k < _PB_M; k++)
         B[i][j] += A[k][i] * B[k][j];
for (i = 0; i < _PB_M; i++)   // <-- split here at i level... 
