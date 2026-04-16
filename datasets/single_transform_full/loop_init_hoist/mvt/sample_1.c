#pragma scop
  for (i = 0; i < _PB_N; i++)
    for (j = 0; j < _PB_N; j++)
      x1[i] = x1[i] + A[i][j] * y_1[j];
  for (i = 0; i < _PB_N; i++) {
    DATA_TYPE tmp = x2[i];
    for (j = 0; j < _PB_N; j++)
      tmp = tmp + A[j][i] * y_2[j];
    x2[i] = tmp;
  }
#pragma endscop
