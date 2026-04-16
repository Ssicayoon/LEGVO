int t = path[i][k] + path[k][j];
path[i][j] = path[i][j] < t ? path[i][j] : t;
