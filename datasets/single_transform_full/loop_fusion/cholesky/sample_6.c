for (j = 0; j < i; j++) {
    // original j<i body
    for (k = 0; k < j; k++) {
        A[i][j] -= A[i][k] * A[j][k];
    }
    A[i][j] /= A[j][j];
    // original k<i body (k renamed to j)
    A[i][i] -= A[i][j] * A[i][j];
}
