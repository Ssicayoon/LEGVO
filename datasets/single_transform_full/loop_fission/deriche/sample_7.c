for (i=0; i<_PB_W; i++)
    for (j=0; j<_PB_H; j++) {
        imgOut[i][j] = c1 * (y1[i][j] + y2[i][j]);
    }
