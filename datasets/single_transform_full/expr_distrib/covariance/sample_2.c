        for (k = 0; k < _PB_N; k++)
	  cov[i][j] += data[k][i] * data[k][j] / (float_n - SCALAR_VAL(1.0));
        cov[j][i] = cov[i][j];
