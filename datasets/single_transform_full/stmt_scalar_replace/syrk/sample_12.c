    for (j = 0; j <= i; j++) {
      DATA_TYPE c_ij = C[i][j];
      c_ij *= beta;
      C[i][j] = c_ij;
    }
