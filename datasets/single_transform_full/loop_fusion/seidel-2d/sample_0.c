#pragma scop
  for (t = 0; t <= _PB_TSTEPS - 1; t++) {
    int ij;
    for (ij = 0; ij < (_PB_N - 2) * (_PB_N - 2); ij++) {
      int i = ij / (_PB_N - 2) + 1;
      int j = ij % (_PB_N - 2) + 1;
      A[i][j] = (A[i-1][j-1] + A[i-1][j] + A[i-1][j+1]
                 + A[i][j-1] + A[i][j] + A[i][j+1]
                 + A[i+1][j-1] + A[i+1][j] + A[i+1][j+1])/SCALAR_VAL(9.0);
    }
  }
#pragma endscop
