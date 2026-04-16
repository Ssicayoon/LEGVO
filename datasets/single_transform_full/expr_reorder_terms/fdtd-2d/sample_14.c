hz[i][j] = hz[i][j] - SCALAR_VAL(0.7)*  (ex[i][j+1] - ex[i][j] +
                           ey[i+1][j] - ey[i][j]);
