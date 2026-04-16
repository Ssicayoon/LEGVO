R[k][j] = SCALAR_VAL(0.0);          // stmt A
for (i = 0; i < _PB_M; i++)        // stmt B: uses R[k][j] (adds to it)
    R[k][j] += Q[i][k] * A[i][j];
for (i = 0; i < _PB_M; i++)        // stmt C: uses R[k][j], Q[i][k], A[i][j]; writes A[i][j]
    A[i][j] = A[i][j] - Q[i][k] * R[k][j];
