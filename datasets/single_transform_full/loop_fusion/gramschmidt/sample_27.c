      for (i = 0; i < _PB_M; i++) {
        nrm += A[i][k] * A[i][k];
        Q[i][k] = A[i][k] / R[k][k];  // NOT safe
