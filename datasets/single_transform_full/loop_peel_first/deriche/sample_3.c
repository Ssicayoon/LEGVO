for (j=_PB_H-1; j>=0; j--) {
    y2[i][j] = a3*xp1 + a4*xp2 + b1*yp1 + b2*yp2;
    xp2 = xp1;
    xp1 = imgIn[i][j];
    yp2 = yp1;
    yp1 = y2[i][j];
}
