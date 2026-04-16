B[i][j] = alpha * B[i][j];  // first scale original
for (k = i+1; k < _PB_M; k++)
   B[i][j] += alpha * A[k][i] * B[k][j];  // distribute alpha in
