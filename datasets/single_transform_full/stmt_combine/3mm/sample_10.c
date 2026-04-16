  /* G := E*F */
  for (i = 0; i < _PB_NI; i++)
    for (j = 0; j < _PB_NL; j++)
      {
	G[i][j] = E[i][0] * F[0][j];
	for (k = 1; k < _PB_NJ; ++k)
	  G[i][j] += E[i][k] * F[k][j];
      }
