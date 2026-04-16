    for (j = 0; j < _PB_NJ; j++)
      C[i][j] = C[i][j] * (beta - POLYBENCH_C(1.0)) + C[i][j];
