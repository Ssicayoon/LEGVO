#pragma scop
  for (i = 0; i < _PB_N; i++)
    {
      tmp[i] = SCALAR_VAL(0.0);
      y[i] = SCALAR_VAL(0.0);
      for (j = 0; j < _PB_N; j++)
	{
	  tmp[i] = A[i][j] * x[j] + tmp[i];
	  y[i] = B[i][j] * x[j] + y[i];
	}
      y[i] = alpha * tmp[i] + beta * y[i];
    }
#pragma endscop
