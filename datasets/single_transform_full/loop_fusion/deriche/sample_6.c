for (j=0; j<_PB_H; j++) {
    // y1 part
    tm1 = ...; ym1 = ...; ym2 = ...;
    for (i=0; i<_PB_W; i++) { ... y1 ... }
    // y2 part  
    tp1 = ...; tp2 = ...; yp1 = ...; yp2 = ...;
    for (i=_PB_W-1; i>=0; i--) { ... y2 ... }
}
