for (k = 0; k < _PB_N; k++)        // outer
  for (i = 0; i < _PB_N; i++)      // middle
    for (j = 0; j < _PB_N; j++)    // inner
      path[i][j] = path[i][j] < path[i][k] + path[k][j] ?
        path[i][j] : path[i][k] + path[k][j];
