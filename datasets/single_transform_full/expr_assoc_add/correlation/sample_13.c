          for (k = 0; k < _PB_N; k++)
            corr[i][j] = data[k][i] * (data[k][j] + corr[i][j]) - data[k][i] * corr[i][j] + corr[i][j];
