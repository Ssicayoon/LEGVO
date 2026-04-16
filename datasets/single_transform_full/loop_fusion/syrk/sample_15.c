for (i = 0; i < _PB_N; i++) {
    for (k = 0; k < _PB_M; k++) {
        for (j = 0; j <= i; j++) {
            if (k == 0) C[i][j] *= beta;
            C[i][j] += alpha * A[i][k] * A[j][k];
        }
    }
}
