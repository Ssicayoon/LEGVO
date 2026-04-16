R[k][j] = 0.0;
for (i) R[k][j] += Q[i][k] * A[i][j];   // loop A
for (i) A[i][j] = A[i][j] - Q[i][k] * R[k][j];  // loop B
