for (i=1; i<_PB_N-1; i++) {
  u[i][0] = SCALAR_VAL(1.0);
  p[i][0] = SCALAR_VAL(0.0);  // <-- this is the target for variant 23
  q[i][0] = u[i][0];
  ...
}
