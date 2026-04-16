for (k = 0; k < i; k++) {
   C[k][j] += alpha*B[i][j] * A[i][k];  // writes C[k][j]
   temp2 += B[k][j] * A[i][k];           // accumulates temp2
}
