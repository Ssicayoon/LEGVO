w = A[i][j];
for (k = 0; k < j; k++) {
   w -= A[i][k] * A[k][j];
}
A[i][j] = w / A[j][j];
