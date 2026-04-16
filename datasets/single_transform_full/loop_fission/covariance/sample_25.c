for (i = 0; i < _PB_M; i++)
    for (j = i; j < _PB_M; j++)
      {
        cov[i][j] = SCALAR_VAL(0.0);          // stmt 1
        for (k = 0; k < _PB_N; k++)
	  cov[i][j] += data[k][i] * data[k][j];  // stmt 2 (depends on stmt 1)
        cov[i][j] /= (float_n - SCALAR_VAL(1.0)); // stmt 3 (depends on stmts 1,2)
        cov[j][i] = cov[i][j];                // stmt 4 (depends on stmt 3)
      }
