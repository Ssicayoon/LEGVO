      for (i = 0; i < _PB_NX; i++)
	for (j = 1; j < _PB_NY; j++)
	  ex[i][j] -= SCALAR_VAL(0.5)*(hz[i][j]-hz[i][j-1]);
