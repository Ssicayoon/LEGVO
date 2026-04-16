    for (j = 0; j < _PB_NJ; j++) {
        DATA_TYPE cij = C[i][j];
        cij *= beta;
        C[i][j] = cij;
    }
