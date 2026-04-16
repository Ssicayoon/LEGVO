int temp = path[i][k] + path[k][j];
path[i][j] = path[i][j] < temp ? path[i][j] : temp;
