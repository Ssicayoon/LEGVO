for (i=_PB_W-1; i>=0; i--) {
    y2[i][j] = a7*tp1 + a8*tp2 + b1*yp1 + b2*yp2;
    tp2 = tp1;
    tp1 = imgOut[i][j];
    ...
}
