for (i = 0; i < _PB_M; i++)
    for (j = i; j < _PB_M; j++)
      {
        cov[i][j] = SCALAR_VAL(0.0);  // init inside inner loop
        for (k = 0; k < _PB_N; k++)
          cov[i][j] += data[k][i] * data[k][j];
        ...
      }
