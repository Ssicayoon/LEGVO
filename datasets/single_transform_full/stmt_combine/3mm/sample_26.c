  for (i = 0; i < _PB_NJ; i++)
    for (j = 0; j < _PB_NL; j++)
      {
	DATA_TYPE temp = SCALAR_VAL(0.0);
	for (k = 0; k < _PB_NM; ++k)
	  temp += C[i][k] * D[k][j];
	F[i][j] = temp;
      }
