for (k = 0; k < _PB_N; k++)
  for(i = 0; i < _PB_N; i++) {
    DATA_TYPE path_ik = path[i][k];  // hoist out of j loop
    for (j = 0; j < _PB_N; j++)
      path[i][j] = path[i][j] < path_ik + path[k][j] ?
        path[i][j] : path_ik + path[k][j];
  }
