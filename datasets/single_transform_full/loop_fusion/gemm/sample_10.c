for (i ...) {
    for (j = 0; j < _PB_NJ; j++)   // loop A: C[i][j] *= beta
    for (k = 0; k < _PB_NK; k++) {
       for (j = 0; j < _PB_NJ; j++) // loop B: C[i][j] += ...
    }
}
