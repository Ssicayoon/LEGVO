F[i][j] = C[i][0] * D[0][j];
for (k = 1; k < _PB_NM; ++k)
  F[i][j] += C[i][k] * D[k][j];
