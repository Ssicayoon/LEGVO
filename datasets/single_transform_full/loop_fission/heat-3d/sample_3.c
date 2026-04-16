        for (i = 1; i < _PB_N-1; i++) {
           for (j = 1; j < (_PB_N-1)/2+1; j++) {  // first half
               for (k = 1; k < _PB_N-1; k++) { A[i][j][k] = ...; }
           }
           for (j = (_PB_N-1)/2+1; j < _PB_N-1; j++) {  // second half
               ...
           }
        }
