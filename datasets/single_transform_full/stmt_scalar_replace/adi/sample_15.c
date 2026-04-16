      for (j=_PB_N-2; j>=1; j--) {
        DATA_TYPE v_next = v[j+1][i];
        v[j][i] = p[i][j] * v_next + q[i][j];
      }
