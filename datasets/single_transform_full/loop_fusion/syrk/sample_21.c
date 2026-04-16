for (i = 0; i < _PB_N; i++) {
    // merge: C[i][j] *= beta combined with k=0 contribution
    for (j = 0; j <= i; j++) {
        C[i][j] *= beta;
        C[i][j] += alpha * A[i][0] * A[j][0];
    }
    for (k = 1; k < _PB_M; k++) {
        for (j = 0; j <= i; j++)
            C[i][j] += alpha * A[i][k] * A[j][k];
    }
}
