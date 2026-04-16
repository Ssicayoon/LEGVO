for (j = 0; j < i; j++) {
    for (k = 0; k < j; k++) {
        A[i][j] -= A[i][k] * A[j][k];
    }
    A[i][j] /= A[j][j];  // This statement after the k-loop prevents swapping j and k here
}
