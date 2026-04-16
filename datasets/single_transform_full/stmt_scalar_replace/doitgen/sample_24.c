for (s = 0; s < _PB_NP; s++) {
    DATA_TYPE a_rqs = A[r][q][s];
    sum[p] += a_rqs * C4[s][p];
}
