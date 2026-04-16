  for (i = 0; i < _PB_N; i++)
    for (j = 0; j < _PB_N; j++) {
      DATA_TYPE tmp = A[i][j];
      tmp = tmp + u1[i] * v1[j] + u2[i] * v2[j];
      A[i][j] = tmp;
    }
