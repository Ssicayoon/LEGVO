for (i = 0; i < _PB_NX - 1; i++)
  for (j = 0; j < _PB_NY - 1; j++)
    hz[i][j] = hz[i][j] - SCALAR_VAL(0.7)*(ex[i][j+1] - ex[i][j] + ey[i+1][j] - ey[i][j]);
