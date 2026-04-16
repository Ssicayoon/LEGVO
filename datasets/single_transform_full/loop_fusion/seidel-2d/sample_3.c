#pragma scop
  for (t = 0; t <= _PB_TSTEPS - 1; t++)
    for (ij = 0; ij <= (_PB_N - 2)*(_PB_N - 2) - 1; ij++) {
      int i = ij / (_PB_N - 2) + 1;
      int j = ij % (_PB_N - 2) + 1;
      A[i][j] = ...
    }
#pragma endscop
