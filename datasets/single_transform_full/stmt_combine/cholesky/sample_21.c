for (k = 0; k < i; k++) {
   A[i][i] -= A[i][k] * A[i][k];
}
A[i][i] = SQRT_FUN(A[i][i]);
