for (j = 1; j <= i; j++)
    x[i] -= L[i][j-1] * x[j-1];
