      for (j=_PB_N-3; j>=0; j--) {
        u[i][j+1] = p[i][j+1] * u[i][j+2] + q[i][j+1];
      }
