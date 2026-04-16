for (i = 0; i < _PB_N; i++)
  {
    tmp[i] = 0.0;
    y[i] = 0.0;
    for (j = 0; j < _PB_N; j++)
      { tmp[i] += ...; y[i] += ...; }
    y[i] = alpha * tmp[i] + beta * y[i];
  }
