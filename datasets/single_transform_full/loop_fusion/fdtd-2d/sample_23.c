for (i = 0; i < _PB_NX; i++)
  for (j = 0; j < _PB_NY; j++)
    if (i == 0) ey[0][j] = _fict_[t];
    else ey[i][j] = ey[i][j] - SCALAR_VAL(0.5)*(hz[i][j]-hz[i-1][j]);
