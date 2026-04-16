x[i] = b[i];
for (j = 0; j < i; j++)
    x[i] -= L[i][j] * x[j];
x[i] = x[i] / L[i][i];
