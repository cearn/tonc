//
// Testing iwram versions of chr4_drawg_b1cts. Let's see what the compiler can make of it.
// This is the base version (ARM/iwram)

#define GEN_CODE_SEC IWRAM_CODE 

#define GEN_PROCNAME_BASE chr4c_drawg_b1cts_c_base_arm_iwram
#define GEN_PROCNAME_FAST chr4c_drawg_b1cts_c_fast_arm_iwram

#include "chr4c_drawg_b1cts_c_base.c"
