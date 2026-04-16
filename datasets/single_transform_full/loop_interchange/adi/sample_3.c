for (i=1; i<_PB_N-1; i++) {
  u[i][0] = ...;
  p[i][0] = ...;
  q[i][0] = ...;
  for (j=1; j<_PB_N-1; j++) {  // forward j loop
    p[i][j] = ...;
    q[i][j] = ...;
  }
  u[i][_PB_N-1] = ...;
  for (j=_PB_N-2; j>=1; j--) {  // backward j loop
    u[i][j] = p[i][j] * u[i][j+1] + q[i][j];
  }
}
