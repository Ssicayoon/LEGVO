for (j = 0; j < i; j++) {
    // original j loop body
    for (k = 0; k < j; k++) {
       A[i][j] -= A[i][k] * A[j][k];
    }
    A[i][j] /= A[j][j];
    // original k loop body (using j as the index)
    A[i][i] -= A[i][j] * A[i][j];
}
