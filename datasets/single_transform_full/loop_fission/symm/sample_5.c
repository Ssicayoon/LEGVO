for (k = 0; k < i; k++) {
   C[k][j] += alpha*B[i][j] * A[i][k];  // statement 1: updates C[k][j]
   temp2 += B[k][j] * A[i][k];           // statement 2: updates temp2
}
