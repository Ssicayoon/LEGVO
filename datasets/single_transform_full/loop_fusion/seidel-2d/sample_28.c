static
void kernel_seidel_2d(int tsteps,
		      int n,
		      DATA_TYPE POLYBENCH_2D(A,N,N,n,n))
{
  int t, i, j, ij;

#pragma scop
  for (t = 0; t <= _PB_TSTEPS - 1; t++)
    for (ij = 0; ij <= (_PB_N - 2)*(_PB_N - 2) - 1; ij++) {
      i = ij / (_PB_N - 2) + 1;
      j = ij % (_PB_N - 2) + 1;
      A[i][j] = (A[i-1][j-1] + A[i-1][j] + A[i-1][j+1]
		   + A[i][j-1] + A[i][j] + A[i][j+1]
		   + A[i+1][j-1] + A[i+1][j] + A[i+1][j+1])/SCALAR_VAL(9.0);
    }
#pragma endscop
}
