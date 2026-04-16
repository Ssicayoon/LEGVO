cov[i][j] = SCALAR_VAL(0.0);
for (k = 0; k < _PB_N; k++)
    cov[i][j] += data[k][i] * data[k][j];
