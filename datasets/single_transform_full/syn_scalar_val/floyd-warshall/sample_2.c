path[i][j] = path[i][k] + path[k][j] - path[i][j] < SCALAR_VAL(0.0) ?
    path[i][j] : path[i][k] + path[k][j];
