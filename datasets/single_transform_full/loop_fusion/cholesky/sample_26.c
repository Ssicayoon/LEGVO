for (j = 0; j < i; j++) {
    for (k = 0; k < j; k++) {
        A[i][j] -= A[i][k] * A[j][k];
    }
    A[i][j] /= A[j][j];
    A[i][i] -= A[i][j] * A[i][j];  // merged from k loop, using j as k
}
