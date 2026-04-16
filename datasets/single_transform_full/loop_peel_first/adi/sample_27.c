for (j=1; j<_PB_N-1; j++) {
    p[i][j] = -f / (d*p[i][j-1]+e);
    q[i][j] = (-a*v[i-1][j]+(SCALAR_VAL(1.0)+SCALAR_VAL(2.0)*a)*v[i][j] - c*v[i+1][j]-d*q[i][j-1])/(d*p[i][j-1]+e);
}
