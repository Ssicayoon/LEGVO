static
void kernel_heat_3d(int tsteps,
		      int n,
		      DATA_TYPE POLYBENCH_3D(A,N,N,N,n,n,n),
		      DATA_TYPE POLYBENCH_3D(B,N,N,N,n,n,n))
{
  int t, i, j, k;

#pragma scop
    for (t = 1; t <= TSTEPS; t++) {
        for (i = 1; i < (_PB_N-1)/2; i++) {
            for (j = 1; j < _PB_N-1; j++) {
                for (k = 1; k < _PB_N-1; k++) {
                    B[i][j][k] =   SCALAR_VAL(0.125) * (A[i+1][j][k] - SCALAR_VAL(2.0) * A[i][j][k] + A[i-1][j][k])
                                 + SCALAR_VAL(0.125) * (A[i][j+1][k] - SCALAR_VAL(2.0) * A[i][j][k] + A[i][j-1][k])
                                 + SCALAR_VAL(0.125) * (A[i][j][k+1] - SCALAR_VAL(2.0) * A[i][j][k] + A[i][j][k-1])
                                 + A[i][j][k];
                }
            }
        }
