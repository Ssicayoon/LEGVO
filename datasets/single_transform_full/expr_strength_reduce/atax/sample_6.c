y[i] = 0;
tmp[i] = SCALAR_VAL(0.0);
tmp[i] = tmp[i] + A[i][j] * x[j];
y[j] = y[j] + A[i][j] * tmp[i];
