    for (j=0; j<_PB_H; j++) {
        tm1 = SCALAR_VAL(0.0);
        ym1 = SCALAR_VAL(0.0);
        ym2 = SCALAR_VAL(0.0);
        for (i=1; i<=_PB_W; i++) {
            y1[i-1][j] = a5*imgOut[i-1][j] + a6*tm1 + b1*ym1 + b2*ym2;
            tm1 = imgOut[i-1][j];
            ym2 = ym1;
            ym1 = y1[i-1][j];
        }
    }
