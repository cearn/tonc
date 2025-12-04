
#include <tonc.h>

// C equivalent of memcpy32, using 32-byte blocks.
IWRAM_CODE void memcpy32_c_iwram(void *dst, const void *src, uint wdcount)
{
	const uint STRIDE = sizeof(BLOCK)/4;
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