for (j=0; j<_PB_H; j++) {
    tp1 = SCALAR_VAL(0.0);
    tp2 = SCALAR_VAL(0.0);
    yp1 = SCALAR_VAL(0.0);
    yp2 = SCALAR_VAL(0.0);
    for (i=_PB_W-1; i>=0; i--) {
        y2[i][j] = a7*tp1 + a8*tp2 + b1*yp1 + b2*yp2;
        ...
    }
}
