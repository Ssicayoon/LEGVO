DATA_TYPE sum = path[i][k] + path[k][j];
if (path[i][j] > sum)
    path[i][j] = sum;
