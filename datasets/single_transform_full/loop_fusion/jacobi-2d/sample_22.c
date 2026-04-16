for (i = 1; i < _PB_N - 1; i++) {
    for (j = 1; j < _PB_N - 1; j++)
        B[i][j] = ...;
    for (j = 1; j < _PB_N - 1; j++)
        A[i][j] = ...;  // reads B[i-1], B[i], B[i+1] — NOT safe
}
