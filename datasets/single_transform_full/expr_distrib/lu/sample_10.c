A[i][j] -= A[i][k] * A[k][j];  // for k = 0..j-1
A[i][j] /= A[j][j];
