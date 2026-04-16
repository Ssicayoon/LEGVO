for (t = 0; t < _PB_TSTEPS; t++)
  {
    for (i = 1; i < _PB_N - 1; i++)   // loop A: computes B from A
      B[i] = ...
    for (i = 1; i < _PB_N - 1; i++)   // loop B: computes A from B
      A[i] = ...
  }
