    for (i=0; i<_PB_W; i++)
        for (j=0; j<_PB_H; j++) {
            DATA_TYPE _y1_ij = y1[i][j];
            DATA_TYPE _y2_ij = y2[i][j];
            imgOut[i][j] = c2*(_y1_ij + _y2_ij);
        }
