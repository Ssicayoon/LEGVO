x[i] = b[i];
x[i] -= L[i][j] * x[j];
x[i] = x[i] / L[i][i];
