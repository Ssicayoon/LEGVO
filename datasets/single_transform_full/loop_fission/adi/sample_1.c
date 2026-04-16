for (i=1; i<_PB_N-1; i++) {
  u[i][0] = SCALAR_VAL(1.0);
  p[i][0] = SCALAR_VAL(0.0);
  q[i][0] = u[i][0];
  ...
  u[i][_PB_N-1] = SCALAR_VAL(1.0);
  for (j=_PB_N-2; j>=1; j--) {
    u[i][j] = p[i][j] * u[i][j+1] + q[i][j];
  }
}
