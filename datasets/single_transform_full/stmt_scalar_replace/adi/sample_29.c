      for (j=_PB_N-2; j>=1; j--) {
        DATA_TYPE uij1 = u[i][j+1];
        DATA_TYPE uij = p[i][j] * uij1 + q[i][j];
        u[i][j] = uij;
      }
