G[i][j] = SCALAR_VAL(0.0);
for (k = 0; k < _PB_NJ; ++k)
  G[i][j] += E[i][k] * F[k][j];
