w = b[i];
for (j = 0; j < i; j++)
   w -= A[i][j] * y[j];
y[i] = w;
