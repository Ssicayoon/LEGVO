path[i][j] = path[i][j] + (-(path[i][k] + path[k][j])) < 0 ?
    path[i][j] : path[i][k] + path[k][j];
