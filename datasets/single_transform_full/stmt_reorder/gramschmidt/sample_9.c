R[k][j] = SCALAR_VAL(0.0);
for (i = 0; i < _PB_M; i++)
    R[k][j] += Q[i][k] * A[i][j];
for (i = 0; i < _PB_M; i++)
    A[i][j] = A[i][j] - Q[i][k] * R[k][j];
