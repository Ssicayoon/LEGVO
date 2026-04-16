y1[i][j] = a5*imgOut[i][j] + a6*tm1 + b1*ym1 + b2*ym2;
tm1 = imgOut[i][j];
ym2 = ym1;
ym1 = y1[i][j];  // ym1 = y1[i][j] uses y1[i][j] which was just computed
