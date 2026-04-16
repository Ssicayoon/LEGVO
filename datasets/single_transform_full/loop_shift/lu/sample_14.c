for (k = 1; k <= i; k++) {
   A[i][j] -= A[i][k-1] * A[k-1][j];
}
