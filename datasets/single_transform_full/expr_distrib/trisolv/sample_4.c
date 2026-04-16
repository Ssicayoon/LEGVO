#pragma scop
  for (i = 0; i < _PB_N; i++)
    {
      x[i] = b[i] / L[i][i];
      for (j = 0; j < i; j++)
        x[i] -= (L[i][j] * x[j]) / L[i][i];
    }
#pragma endscop
