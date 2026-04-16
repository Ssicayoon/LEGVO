A[i][j] -= A[i][k] * A[k][j];  // in loop
A[i][j] /= A[j][j];             // after loop
