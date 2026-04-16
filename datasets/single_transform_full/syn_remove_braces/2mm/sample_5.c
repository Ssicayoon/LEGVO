#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "2mm.h"
static
void init_array(int ni, int nj, int nk, int nl,DATA_TYPE *alpha,DATA_TYPE *beta,DATA_TYPE POLYBENCH_2D(A,NI,NK,ni,nk),DATA_TYPE POLYBENCH_2D(B,NK,NJ,nk,nj),DATA_TYPE POLYBENCH_2D(C,NJ,NL,nj,nl),DATA_TYPE POLYBENCH_2D(D,NI,NL,ni,nl)){int i,j;*alpha=1.5;*beta=1.2;for(i=0;i<ni;i++)for(j=0;j<nk;j++)A[i][j]=(DATA_TYPE)((i*j+1)%ni)/ni;for(i=0;i<nk;i++)for(j=0;j<nj;j++)B[i][j]=(DATA_TYPE)(i*(j+1)%nj)/nj;for(i=0;i<nj;i++)for(j=0;j<nl;j++)C[i][j]=(DATA_TYPE)((i*(j+3)+1)%nl)/nl;for(i=0;i<ni;i++)for(j=0;j<nl;j++)D[i][j]=(DATA_TYPE)(i*(j+2)%nk)/nk;}
