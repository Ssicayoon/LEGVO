for (i = 0; i < _PB_N; i++) {
    for (j = 0; j < i; j++) {       // loop A
       for (k = 0; k < j; k++) {    // loop B (innermost of A)
          A[i][j] -= A[i][k] * A[k][j];
       }
        A[i][j] /= A[j][j];
    }
   for (j = i; j < _PB_N; j++) {   // loop C
       for (k = 0; k < i; k++) {    // loop D (innermost of C)
          A[i][j] -= A[i][k] * A[k][j];
       }
    }
}
