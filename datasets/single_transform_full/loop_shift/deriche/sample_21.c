    for (i=1; i<=_PB_W; i++)
        for (j=0; j<_PB_H; j++) {
            imgOut[i-1][j] = c1 * (y1[i-1][j] + y2[i-1][j]);
        }
