      for (i = 1; i < _PB_NX; i++)
	for (j = 0; j < _PB_NY; j++)
	  ey[i][j] = ey[i][j] - (hz[i][j]-hz[i-1][j])*SCALAR_VAL(0.5);
