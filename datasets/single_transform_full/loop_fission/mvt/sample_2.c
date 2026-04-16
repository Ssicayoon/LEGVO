for (i = 0; i < _PB_N/2; i++)
  for (j = 0; j < _PB_N; j++)
    x2[i] = x2[i] + A[j][i] * y_2[j];
for (i = _PB_N/2; i < _PB_N; i++)
  for (j = 0; j < _PB_N; j++)
    x2[i] = x2[i] + A[j][i] * y_2[j];
