#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <polybench.h>
#include "fdtd-2d.h"

static void init_array (int tmax, int nx, int ny, DATA_TYPE POLYBENCH_2D(ex,NX,NY,nx,ny), DATA_TYPE POLYBENCH_2D(ey,NX,NY,nx,ny), DATA_TYPE POLYBENCH_2D(hz,NX,NY,nx,ny), DATA_TYPE POLYBENCH_1D(_fict_,TMAX,tmax)) { int i, j; for (i = 0; i < tmax; i++) _fict_[i] = (DATA_TYPE) i; for (i = 0; i < nx; i++) for (j = 0; j < ny; j++) { ex[i][j] = ((DATA_TYPE) i*(j+1)) / nx; ey[i][j] = ((DATA_TYPE) i*(j+2)) / ny; hz[i][j] = ((DATA_TYPE) i*(j+3)) / nx; } }
static void print_array(int nx, int ny, DATA_TYPE POLYBENCH_2D(ex,NX,NY,nx,ny), DATA_TYPE POLYBENCH_2D(ey,NX,NY,nx,ny), DATA_TYPE POLYBENCH_2D(hz,NX,NY,nx,ny)) { int i, j; POLYBENCH_DUMP_START; POLYBENCH_DUMP_BEGIN("ex"); for (i = 0; i < nx; i++) for (j = 0; j < ny; j++) { if ((i * nx + j) % 20 == 0) fprintf(POLYBENCH_DUMP_TARGET, "\n"); fprintf(POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, ex[i][j]); } POLYBENCH_DUMP_END("ex"); POLYBENCH_DUMP_FINISH; POLYBENCH_DUMP_BEGIN("ey"); for (i = 0; i < nx; i++) for (j = 0; j < ny; j++) { if ((i * nx + j) % 20 == 0) fprintf(POLYBENCH_DUMP_TARGET, "\n"); fprintf(POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, ey[i][j]); } POLYBENCH_DUMP_END("ey"); POLYBENCH_DUMP_BEGIN("hz"); for (i = 0; i < nx; i++) for (j = 0; j < ny; j++) { if ((i * nx + j) % 20 == 0) fprintf(POLYBENCH_DUMP_TARGET, "\n"); fprintf(POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, hz[i][j]); } POLYBENCH_DUMP_END("hz"); }
