    for (j=0; j<_PB_H; j++) {
        tm1 = SCALAR_VAL(0.0); ym1 = SCALAR_VAL(0.0); ym2 = SCALAR_VAL(0.0);
        for (i=0; i<_PB_W; i++) { ... y1 ... }
        tp1 = SCALAR_VAL(0.0); tp2 = SCALAR_VAL(0.0); yp1 = SCALAR_VAL(0.0); yp2 = SCALAR_VAL(0.0);
        for (i=_PB_W-1; i>=0; i--) { ... y2 ... }
    }
