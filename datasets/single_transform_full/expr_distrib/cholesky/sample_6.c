A[i][j] -= A[i][k] * A[j][k];  // accumulated over k
A[i][j] /= A[j][j];
