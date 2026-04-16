#pragma scop
  for (i = 0; i < _PB_N; i++)
    for (j = 0; j <= i; j++)
      C[i][j] *= beta;
  for (i = 0; i < _PB_N; i++)
    for (k = 0; k < _PB_M; k++)
      for (j = 0; j <= i; j++)
        {
          C[i][j] += A[j][k]*alpha*B[i][k] + B[j][k]*alpha*A[i][k];
        }
#pragma endscop
