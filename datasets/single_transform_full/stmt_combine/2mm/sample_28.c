  for (i = 0; i < _PB_NI; i++)
    for (j = 0; j < _PB_NL; j++)
      {
	D[i][j] = D[i][j] * beta + tmp[i][0] * C[0][j];
	for (k = 1; k < _PB_NJ; ++k)
	  D[i][j] += tmp[i][k] * C[k][j];
      }
