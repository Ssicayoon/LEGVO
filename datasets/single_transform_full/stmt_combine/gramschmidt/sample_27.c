      R[k][k] = SCALAR_VAL(0.0);
      for (i = 0; i < _PB_M; i++)
        R[k][k] += A[i][k] * A[i][k];
      R[k][k] = SQRT_FUN(R[k][k]);
