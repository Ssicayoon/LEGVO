          for (k = 0; k < _PB_N; k++)
            corr[i][j] = corr[i][j] + (data[k][i] * data[k][j] + SCALAR_VAL(0.0));
