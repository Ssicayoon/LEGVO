  for (j = 0; j < _PB_M; j++)
    {
      mean[j] = SCALAR_VAL(0.0);
      for (i = 0; i < _PB_N; i++)
        mean[j] += data[i][j];
      mean[j] /= float_n;
      for (i = 0; i < _PB_N; i++)
        data[i][j] -= mean[j];
    }
