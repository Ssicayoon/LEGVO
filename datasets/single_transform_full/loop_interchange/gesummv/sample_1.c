for (i = 0; i < _PB_N; i++)
  {
    tmp[i] = 0; y[i] = 0;
    for (j = 0; j < _PB_N; j++)
      { tmp[i] += A[i][j]*x[j]; y[i] += B[i][j]*x[j]; }
    y[i] = alpha*tmp[i] + beta*y[i];
  }
