      for (i = 0; i < _PB_M; i++)
        nrm += A[i][k] * A[i][k];
      R[k][k] = SQRT_FUN(nrm);  /* swap: nrm=0 moved after */
      nrm = SCALAR_VAL(0.0);    /* reset nrm after use */
