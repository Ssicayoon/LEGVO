for (i = 0; i < _PB_NI; i++)
  for (j = 0; j < _PB_NL; j++)
    {
      D[i][j] *= beta;                    // statement 1
      for (k = 0; k < _PB_NJ; ++k)
        D[i][j] += tmp[i][k] * C[k][j];  // statement 2 (depends on statement 1)
    }
