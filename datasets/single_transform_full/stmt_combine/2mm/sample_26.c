  for (i = 0; i < _PB_NI; i++)
    for (j = 0; j < _PB_NL; j++)
      {
	D[i][j] = beta * D[i][j];
	for (k = 0; k < _PB_NJ; ++k)
	  D[i][j] += tmp[i][k] * C[k][j];
      }
