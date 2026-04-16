                    B[i][j][k] =   SCALAR_VAL(0.125) * (A[i+1][j][k] - SCALAR_VAL(2.0) * A[i][j][k] + A[i-1][j][k])
                                 + SCALAR_VAL(0.125) * (A[i][j+1][k] - SCALAR_VAL(2.0) * A[i][j][k] + A[i][j-1][k])
                                 + SCALAR_VAL(0.125) * (A[i][j][k+1] + (-SCALAR_VAL(2.0) * A[i][j][k] - (-A[i][j][k-1])))
                                 + A[i][j][k];
