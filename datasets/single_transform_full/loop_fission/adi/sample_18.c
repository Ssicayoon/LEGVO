// Split: separate v[0][i] initialization from the rest of column sweep
for (i=1; i<_PB_N-1; i++) {
    v[0][i] = SCALAR_VAL(1.0);
}
for (i=1; i<_PB_N-1; i++) {
    p[i][0] = SCALAR_VAL(0.0);
    q[i][0] = v[0][i];
    // ... rest
}
