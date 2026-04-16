/* G := E*F */
for (i = 0; i < _PB_NI; i++)
  for (j = 0; j < _PB_NL; j++)
    {
      DATA_TYPE tmp = SCALAR_VAL(0.0);
      for (k = 0; k < _PB_NJ; ++k)
        tmp += E[i][k] * F[k][j];
      G[i][j] = tmp;
    }
