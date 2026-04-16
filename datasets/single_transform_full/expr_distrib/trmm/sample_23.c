B[i][j] = alpha * B[i][j];
for (k = i+1; k < _PB_M; k++)
   B[i][j] += alpha * A[k][i] * B[k][j];
