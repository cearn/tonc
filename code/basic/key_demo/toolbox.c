//
// toolbox.c
// 
// Tools source for key_demo
// 
// (20060922-20251227, cearn)
//
// === NOTES ===
// * This is a _small_ set of typedefs, #defines and inlines that can 
//   be found in libtonc, and might not represent the final forms.

#include "toolbox.h"

// === (tonc_core.c) ===========================================================================

u16 __key_curr= 0, __key_prev= 0;
COLOR *vid_page= vid_mem_back;

typedef struct { u32 data[8]; } BLOCK;

void memcpy32(void *dst, const void *src, uint wdcount)
{
	const uint STRIDE= sizeof(BLOCK)/4;
	u32 blkN= wdcount/STRIDE, wdN= wdcount%STRIDE;
	u32 *dstw= (u32*)dst, *srcw= (u32*)src;
	if(blkN)
	{
		// 8-word copies
		BLOCK *dst2= (BLOCK*)dst, *src2= (BLOCK*)src;
		while(blkN--)
			*dst2++ = *src2++;
		dstw= (u32*)dst2;  srcw= (u32*)src2;
	}
	// Residual words
	while(wdN--)
		*dstw++ = *srcw++;
}
