for (i = 0; i < _PB_N; i++) {
  DATA_TYPE tmp = 0;
  for (j = 0; j < _PB_N; j++)
    tmp = tmp + A[i][j] * x[j];
  w[i] = w[i] + alpha * tmp;
}
