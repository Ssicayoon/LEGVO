// Split: first loop sets boundaries, second does computation
for (i=1; i<_PB_N-1; i++) {
  v[0][i] = SCALAR_VAL(1.0);
  v[_PB_N-1][i] = SCALAR_VAL(1.0);
}
for (i=1; i<_PB_N-1; i++) {
  p[i][0] = SCALAR_VAL(0.0);
  q[i][0] = v[0][i];
  for (j=1; j<_PB_N-1; j++) { ... }
  for (j=_PB_N-2; j>=1; j--) { ... }
}
