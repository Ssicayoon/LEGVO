      for (j=_PB_N-2; j>=1; j--) {
        DATA_TYPE u_next = u[i][j+1];
        u[i][j] = p[i][j] * u_next + q[i][j];
      }
