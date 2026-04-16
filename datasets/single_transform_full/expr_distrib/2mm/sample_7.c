	tmp[i][j] = SCALAR_VAL(0.0);
	for (k = 0; k < _PB_NK; ++k)
	  tmp[i][j] += A[i][k] * B[k][j];
      }
