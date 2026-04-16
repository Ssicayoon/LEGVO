  for (i = 0; i < _PB_NI; i++)
    for (j = 0; j < _PB_NJ; j++)
      {
	tmp[i][j] = alpha * A[i][0] * B[0][j];
	for (k = 1; k < _PB_NK; ++k)
	  tmp[i][j] += alpha * A[i][k] * B[k][j];
      }
