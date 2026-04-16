for (i = 0; i < _PB_N; i++) {
    for (j = 0; j < i; j++) {       // Loop A
       for (k = 0; k < j; k++) {    // Loop B (innermost)
          A[i][j] -= A[i][k] * A[k][j];
       }
       A[i][j] /= A[j][j];
    }
    for (j = i; j < _PB_N; j++) {   // Loop C
       for (k = 0; k < i; k++) {    // Loop D (innermost)
          A[i][j] -= A[i][k] * A[k][j];
       }
    }
}
