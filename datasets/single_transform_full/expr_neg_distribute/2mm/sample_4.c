/* D[i][j] += tmp[i][k] * C[k][j] becomes: */
D[i][j] = -((-D[i][j]) - tmp[i][k] * C[k][j]);
