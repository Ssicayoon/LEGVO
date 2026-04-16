#pragma scop
  B[0] = 0.33333 * (A[_PB_N - 1] + A[0] + A[1]);
  B[_PB_N - 1] = 0.33333 * (A[_PB_N - 2] + A[_PB_N - 1] + A[0]);
