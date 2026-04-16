for (i = 0; i < _PB_N; i++) {
    for (j = 0; j < i; j++) {        // Loop A: j from 0 to i-1
       for (k = 0; k < j; k++) {     // Loop B: k from 0 to j-1
          A[i][j] -= A[i][k] * A[k][j];
       }
        A[i][j] /= A[j][j];
    }
   for (j = i; j < _PB_N; j++) {    // Loop C: j from i to N-1
       for (k = 0; k < i; k++) {     // Loop D: k from 0 to i-1
          A[i][j] -= A[i][k] * A[k][j];
       }
    }
}
