      for (j=_PB_N-2; j>=1; j--) {
        DATA_TYPE u_ij = p[i][j] * u[i][j+1] + q[i][j];
        u[i][j] = u_ij;
      }
