for (j = 0; j <= i; j++) {
    C[i][j] *= beta;
    for (k = 0; k < _PB_M; k++)
        C[i][j] += A[j][k]*alpha*B[i][k] + B[j][k]*alpha*A[i][k];
}
