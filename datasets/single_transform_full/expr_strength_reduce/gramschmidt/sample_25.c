nrm += A[i][k] * A[i][k];
R[k][k] = SQRT_FUN(nrm);
Q[i][k] = A[i][k] / R[k][k];
R[k][j] += Q[i][k] * A[i][j];
A[i][j] = A[i][j] - Q[i][k] * R[k][j];
