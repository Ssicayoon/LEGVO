      for (j=_PB_N-2; j>=1; j--) {
        for (i=1; i<_PB_N-1; i++) {
          u[i][j] = p[i][j] * u[i][j+1] + q[i][j];
        }
      }
