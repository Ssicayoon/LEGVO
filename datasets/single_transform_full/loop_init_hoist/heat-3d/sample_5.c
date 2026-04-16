/* Main computational kernel. */
static
void kernel_heat_3d(int tsteps,
		      int n,
		      DATA_TYPE POLYBENCH_3D(A,N,N,N,n,n,n),
		      DATA_TYPE POLYBENCH_3D(B,N,N,N,n,n,n))
{
  int t, i, j, k;

#pragma scop
    for (i = 1; i < _PB_N-1; i++)
        for (j = 1; j < _PB_N-1; j++)
            for (k = 1; k < _PB_N-1; k++)
                B[i][j][k] = A[i][j][k];

    for (t = 1; t <= TSTEPS; t++) {
