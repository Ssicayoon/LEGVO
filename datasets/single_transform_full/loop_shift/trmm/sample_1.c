for (k = i+2; k < _PB_M+1; k++)
   B[i][j] += A[k-1][i] * B[k-1][j];
