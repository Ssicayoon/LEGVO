	F[i][j] = SCALAR_VAL(0.0);
	for (k = 0; k < _PB_NM; ++k)
	  F[i][j] = C[i][k] * D[k][j] + F[i][j];
