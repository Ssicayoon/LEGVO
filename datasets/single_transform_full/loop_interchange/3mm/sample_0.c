/* G := E*F */
for (j = 0; j < _PB_NL; j++)
  for (i = 0; i < _PB_NI; i++)
    {
      G[i][j] = SCALAR_VAL(0.0);
      for (k = 0; k < _PB_NJ; ++k)
        G[i][j] += E[i][k] * F[k][j];
    }
