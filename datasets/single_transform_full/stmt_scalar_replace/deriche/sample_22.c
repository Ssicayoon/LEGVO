    for (j=0; j<_PB_H; j++) {
        tm1 = SCALAR_VAL(0.0);
        ym1 = SCALAR_VAL(0.0);
        ym2 = SCALAR_VAL(0.0);
        for (i=0; i<_PB_W; i++) {
            DATA_TYPE _y1_val = a5*imgOut[i][j] + a6*tm1 + b1*ym1 + b2*ym2;
            y1[i][j] = _y1_val;
            tm1 = imgOut[i][j];
            ym2 = ym1;
            ym1 = _y1_val;
        }
    }
