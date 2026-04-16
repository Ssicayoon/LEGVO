for (i = 0; i < _PB_N; i++) {
    for (j = 0; j < i; j++) {        // first inner section
        for (k = 0; k < j; k++) {    // innermost
            A[i][j] -= A[i][k] * A[k][j];
        }
        A[i][j] /= A[j][j];
    }
    for (j = i; j < _PB_N; j++) {    // second inner section
        for (k = 0; k < i; k++) {    // innermost
            A[i][j] -= A[i][k] * A[k][j];
        }
    }
}
