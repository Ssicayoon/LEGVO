for (i = 0; i < _PB_N; i++) {
    for (j = 0; j < i; j++) {       // first j-loop
        for (k = 0; k < j; k++) {   // k-loop inside first j
        ...
        }
    }
    for (j = i; j < _PB_N; j++) {   // second j-loop
        for (k = 0; k < i; k++) {   // k-loop inside second j
        ...
        }
    }
}
