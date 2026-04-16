/* stddev[j] = 0.0 hoisted out of the j loop */
  for (j = 0; j < _PB_M; j++)
    stddev[j] = SCALAR_VAL(0.0);
  for (j = 0; j < _PB_M; j++)
    {
      for (i = 0; i < _PB_N; i++)
        stddev[j] += ...
