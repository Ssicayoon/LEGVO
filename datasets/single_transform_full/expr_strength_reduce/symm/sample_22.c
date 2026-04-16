C[k][j] += alpha*B[i][j] * A[i][k];
temp2 += B[k][j] * A[i][k];
C[i][j] = beta * C[i][j] + alpha*B[i][j] * A[i][i] + alpha * temp2;
