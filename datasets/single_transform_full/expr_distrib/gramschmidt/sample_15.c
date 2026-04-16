R[k][j] += Q[i][k] * A[i][j]   // step 1
A[i][j] -= Q[i][k] * R[k][j]   // step 2 (but R[k][j] here is the FULL sum, after all i)
