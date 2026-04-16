for (j = 0; j < _PB_N; j++) {
    DATA_TYPE yj = y[j];
    yj = yj + A[i][j] * tmp[i];
    y[j] = yj;
}
