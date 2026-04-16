for (i = 0; i < _PB_N; i++) q[i] = SCALAR_VAL(0.0);
for (j = 0; j < _PB_M; j++)
  for (i = 0; i < _PB_N; i++) { s[j] += r[i]*A[i][j]; q[i] += A[i][j]*p[j]; }
