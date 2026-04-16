path[i][j] = path[i][j] < path[i][k] + path[k][j] ?
    path[i][j] : path[i][k] * 0.5 + path[i][k] * 0.5 + path[k][j];
