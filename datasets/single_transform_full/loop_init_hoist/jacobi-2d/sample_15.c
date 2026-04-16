#pragma scop
  for (i = 0; i < _PB_N; i++) {
    B[i][0] = SCALAR_VAL(0.0);
    B[i][_PB_N-1] = SCALAR_VAL(0.0);
  }
  for (j = 0; j < _PB_N; j++) {
    B[0][j] = SCALAR_VAL(0.0);
    B[_PB_N-1][j] = SCALAR_VAL(0.0);
  }
  for (t = 0; t < _PB_TSTEPS; t++)
