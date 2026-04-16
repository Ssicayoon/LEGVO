tmp[i] = A[i][j] * x[j] + tmp[i];   // inner loop
y[i] = alpha * tmp[i] + beta * y[i]; // outer
