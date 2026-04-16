A[i][j] = A[i][j] + u1[i] * v1[j] + u2[i] * v2[j];
x[i] = x[i] + beta * A[j][i] * y[j];
x[i] = x[i] + z[i];
w[i] = w[i] + alpha * A[i][j] * x[j];
