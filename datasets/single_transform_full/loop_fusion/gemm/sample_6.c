for (i = 0; i < _PB_NI; i++) {
    for (j = 0; j < _PB_NJ; j++)      // loop 1: j
        C[i][j] *= beta;
    for (k = 0; k < _PB_NK; k++) {    // k loop
       for (j = 0; j < _PB_NJ; j++)  // loop 2: j (inside k)
          C[i][j] += alpha * A[i][k] * B[k][j];
    }
}
