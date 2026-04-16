    for (i=0; i<_PB_W; i++)
        for (j=0; j<_PB_H; j++) {
            DATA_TYPE _y1_val = y1[i][j];
            DATA_TYPE _y2_val = y2[i][j];
            DATA_TYPE _acc = c2 * (_y1_val + _y2_val);
            imgOut[i][j] = _acc;
        }
