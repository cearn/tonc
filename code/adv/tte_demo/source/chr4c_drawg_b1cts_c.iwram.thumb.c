//
// Testing iwram versions of chr4c_drawg_b1cts. Let's see what the compiler can make of it.
// This is the Thumb/iwram version

#define GEN_CODE_SEC IWRAM_CODE 

#define GEN_PROCNAME_BASE chr4c_drawg_b1cts_c_base_thumb_iwram
#define GEN_PROCNAME_FAST chr4c_drawg_b1cts_c_fast_thumb_iwram

#include "chr4c_drawg_b1cts_c_base.c"