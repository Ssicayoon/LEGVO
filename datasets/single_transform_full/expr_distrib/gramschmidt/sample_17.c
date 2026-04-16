R[k][j] += Q[i][k] * A[i][j];  // in one i-loop
A[i][j] = A[i][j] - Q[i][k] * R[k][j];  // in another i-loop
