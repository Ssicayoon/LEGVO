for (i = 1; i < _PB_N - 1; i++) {
    for (j = 1; j < _PB_N - 1; j++)
        B[i][j] = ...;
    for (j = 1; j < _PB_N - 1; j++)
        A[i][j] = ...;  // This is NOT equivalent - A[i+1][j] reads next row of B not yet written
}
