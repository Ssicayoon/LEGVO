#pragma scop
  for (t = 0; t <= _PB_TSTEPS - 1; t++)
    for (i = 1; i <= _PB_N - 2; i++)
      for (j = 1; j <= _PB_N - 2; j++)
        A[i][j] = ...;
#pragma endscop
