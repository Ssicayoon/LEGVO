for (i=1; i<_PB_N-1; i++) {
    // Column Sweep body
    v[0][i] = SCALAR_VAL(1.0);
    p[i][0] = SCALAR_VAL(0.0);
    q[i][0] = v[0][i];
    for (j=1; j<_PB_N-1; j++) { ... }
    v[_PB_N-1][i] = SCALAR_VAL(1.0);
    for (j=_PB_N-2; j>=1; j--) { ... }
    // Row Sweep body
    u[i][0] = SCALAR_VAL(1.0);
    p[i][0] = SCALAR_VAL(0.0);
    q[i][0] = u[i][0];
    for (j=1; j<_PB_N-1; j++) { ... }
    u[i][_PB_N-1] = SCALAR_VAL(1.0);
    for (j=_PB_N-2; j>=1; j--) { ... }
}
