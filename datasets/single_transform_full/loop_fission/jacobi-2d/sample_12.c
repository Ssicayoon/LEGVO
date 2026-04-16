for (i = 1; i < _PB_N/2; i++)
    for (j = 1; j < _PB_N - 1; j++)
        B[i][j] = SCALAR_VAL(0.2) * (A[i][j] + A[i][j-1] + A[i][1+j] + A[1+i][j] + A[i-1][j]);
for (i = _PB_N/2; i < _PB_N - 1; i++)
    for (j = 1; j < _PB_N - 1; j++)
        B[i][j] = SCALAR_VAL(0.2) * (A[i][j] + A[i][j-1] + A[i][1+j] + A[1+i][j] + A[i-1][j]);
