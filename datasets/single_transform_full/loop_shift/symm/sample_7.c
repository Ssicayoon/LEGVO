for (k = 1; k <= i; k++) {
   C[k-1][j] += alpha*B[i][j] * A[i][k-1];
   temp2 += B[k-1][j] * A[i][k-1];
}
