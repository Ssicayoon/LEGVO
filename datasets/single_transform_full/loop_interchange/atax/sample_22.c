for (i = 0; i < _PB_M; i++) {
    tmp[i] = SCALAR_VAL(0.0);
    for (j = 0; j < _PB_N; j++)
        tmp[i] = tmp[i] + A[i][j] * x[j];
}
for (j = 0; j < _PB_N; j++)        // swapped: j outer
    for (i = 0; i < _PB_M; i++)    // swapped: i inner
        y[j] = y[j] + A[i][j] * tmp[i];
