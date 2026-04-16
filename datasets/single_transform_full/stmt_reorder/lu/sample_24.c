for (i = 0; i < _PB_N; i++) {
    for (j = 0; j < i; j++) {   // first j-loop
       ...
    }
    for (j = i; j < _PB_N; j++) {  // second j-loop
       ...
    }
}
