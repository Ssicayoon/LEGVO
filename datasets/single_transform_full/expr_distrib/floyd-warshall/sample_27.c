path[i][j] = path[i][j] < path[i][k] + path[k][j] ? path[i][j] : path[i][k] + path[k][j];
