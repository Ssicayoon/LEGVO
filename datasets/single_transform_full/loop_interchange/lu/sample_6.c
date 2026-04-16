for (i = 0; i < _PB_N; i++) {
    for (j = 0; j < i; j++) {        // Loop A: j from 0 to i
        for (k = 0; k < j; k++) {    // Loop B: k from 0 to j
            A[i][j] -= A[i][k] * A[k][j];
        }
        A[i][j] /= A[j][j];
    }
    for (j = i; j < _PB_N; j++) {    // Loop C: j from i to N
        for (k = 0; k < i; k++) {    // Loop D: k from 0 to i
            A[i][j] -= A[i][k] * A[k][j];
        }
    }
}
