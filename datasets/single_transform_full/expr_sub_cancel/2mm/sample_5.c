tmp[i][j] = SCALAR_VAL(0.0);
tmp[i][j] += alpha * A[i][k] * B[k][j];
D[i][j] *= beta;
D[i][j] += tmp[i][k] * C[k][j];
