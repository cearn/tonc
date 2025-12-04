//
//! \file txt_se2.c
//!   Screen entry text demo
//! \date 20051028 - 20251115
//! \author cearn
//
// === NOTES ===

#include <string.h>
#include <stdio.h>

#include <tonc.h>

#include "gba_pic.h"

// Results:

//              hw/mesen    no$     vba
// u16 array    652964      652982
// u32 array    364895      364878
// memcpy       249884      249867
// memcpy32_c   158624      158555
// memcpy32      87675       87719
// DMA           76862       76862

// hw : 674978, 260299, 195171, 86846, 76902
// no$: 672162, 259309, 194608, 85283, 76901
// vba: 557081, 192183, 160367, 80049,   222


// --------------------------------------------------------------------
// FUNCTIONS 
// --------------------------------------------------------------------

// C equivalent of memcpy32, using 32-byte blocks.
void memcpy32_c(void *dst, const void *src, uint wdcount)
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

// --- TESTERS ---

// copy via u16 array.
uint test_u16(void *dstv, const void *srcv, uint size)
{
	u16 *dst= (u16*)dstv, *src= (u16*)srcv;

	profile_start();
	for(uint ii=0; ii<size/2; ii++)
		dst[ii]= src[ii];
	return profile_stop();
}

// copy via u32 array.
uint test_u32(void *dstv, const void *srcv, uint size)
{
	u32 *dst= (u32*)dstv, *src= (u32*)srcv;

	profile_start();
	for(uint ii=0; ii<size/4; ii++)
		dst[ii]= src[ii];
	return profile_stop();
}

// copy via memcpy
uint test_memcpy(void *dstv, const void *srcv, uint size)
{
	profile_start();
	memcpy(dstv, srcv, size);
	return profile_stop();
}

// copy via C version of memcpy32.
uint test_memcpy32_c(void *dstv, const void *srcv, uint size)
{
	profile_start();
	memcpy32_c(dstv, srcv, size/4);
	return profile_stop();
}

IWRAM_CODE void memcpy32_c_iwram(void *dst, const void *src, uint wdcount);

// copy via C version of memcpy32, but ARM/iwram
uint test_memcpy32_c_iwram(void *dstv, const void *srcv, uint size)
{
	profile_start();
	memcpy32_c_iwram(dstv, srcv, size/4);
	return profile_stop();
}


// copy via my own memcpy32.
uint test_memcpy32(void *dstv, const void *srcv, uint size)
{
	profile_start();
	memcpy32(dstv, srcv, size/4);
	return profile_stop();
}

// copy using DMA
uint test_dma(void *dstv, const void *srcv, uint size)
{
	profile_start();
	dma3_cpy(dstv, srcv, size);
	return profile_stop();
}

uint test_CpuFastSet(void *dstv, const void *srcv, uint size)
{
	profile_start();
	CpuFastSet(srcv, dstv, size/4);
	return profile_stop();
}

int main()
{
	irq_init(NULL);
	irq_add(II_VBLANK, NULL);

	REG_WAITCNT = WS_STANDARD;

	struct { 
		const char *name; 
		uint(*proc)(void *dstv, const void *srcv, uint size); 
		uint time;
		char check;
	} tests[]= {
		{ "u16 array", 	test_u16 },
		{ "u32 array", 	test_u32 },
		{ "memcpy", 	test_memcpy },
		{ "memcpy32_c", test_memcpy32_c },
		{ "memcpy32_c_iw", test_memcpy32_c_iwram },
		{ "memcpy32", 	test_memcpy32 },
		{ "CpuFastSet", test_CpuFastSet },
		{ "DMA", 		test_dma },
	};

	for(uint ii=0; ii<countof(tests); ii++)
	{
		tests[ii].time= tests[ii].proc(vid_mem, gba_picBitmap, gba_picBitmapLen);
		tests[ii].check = memcmp(vid_mem, gba_picBitmap, gba_picBitmapLen) ? 'x' : 'v';
	}

	// clear the screenblock I'm about to use.
	SBB_CLEAR(7);

	// init map text
	txt_init_std();
	txt_init_se(0, BG_SBB(7), 0, CLR_YELLOW, 0);

	REG_DISPCNT= DCNT_MODE0 | DCNT_BG0;

	// print results
	char str[32];
	for(uint ii=0; ii<countof(tests); ii++)
	{
		siprintf(str, "%12s %6d %c", tests[ii].name, tests[ii].time, tests[ii].check);
		se_puts(8, 8+8*ii, str, 0);
	}

	while(1)
		VBlankIntrWait();

	return 0;
}
