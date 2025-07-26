///
/// Col-major tile character renderer. 1->4bpp recolored, any size, transparent
/// This is the optimized 'naive' version: still pixel-by-pixel.
/// I just want to see how fast I can get that.
///
/// @file chr4c_drawg_b1cts_base_fast.s
/// @author J Vijn
/// @date 20250719
///
/// === NOTES ===

#define FEATURE_MASK_TEST() 1

#include <tonc_asminc.h>
#include <../src/tte/tte_types.s>

#if 0
	Basic algorithm:

	u32* srcL = [start of glyph]
	u32* dstD = [top-left of dst]
	uint xstart = x&7;
	for(int is; is<charW; is += 8)
	{
		for (int iy=0; iy<charH; iy++)
		{
			dstL = dstD;
			raw = srcL[iy];
			for(int ix=xstart; raw > 0; raw >>= 1, ix++)
			{
				if (~raw&1)
					continue;
				uint shift = (ix&7) * 4;
				uint dstOffset = (ix/8)*dstPitch;
				dstL[dstOffset] = (dstL[dstOffset] &~ (15<<shift)) | ((ink&15)<<shift);
			}

			// 2 options:
			// - keep an index for shift & checking: shift-by-reg is slower
			// - moving shift & mask. Needs to be updated on empties as well.
			dstL++;
		}
		srcD += srcP;
		dstD += dstP;
	}
#endif

// IWRAM_CODE void chr4c_drawg_b1cts_asm_base_arm_iwram(int gid);
BEGIN_FUNC_ARM(chr4c_drawg_b1cts_asm_base_arm_iwram, CSEC_IWRAM)
	stmfd	sp!, {r4-r11, lr}

	ldr		r5,=gp_tte_context
	ldr		r5, [r5]
	
	// Preload dstBase (r4), dstPitch (ip), yx (r6), font (r7)
	ldmia	r5, {r4, ip}
	add		r3, r5, #TTC_cursorX
	ldmia	r3, {r6, r7}

	// Get srcD (r1), width (r11), charH (r2)
	ldmia	r7, {r1, r3}			// Load data, widths
	cmp		r3, #0
	ldrneb	r11, [r3, r0]			// Var charW
	ldreqb	r11, [r7, #TF_charW]	// Fixed charW
	ldrh	r3, [r7, #TF_cellS]
	mla		r1, r3, r0, r1			// srcL
	ldrb	r2, [r7, #TF_charH]		// charH
	ldrb	r10, [r7, #TF_cellH]	// cellH PONDER: load later?

	@ Positional issues: dstD(r0), lsl(r8), lsr(r9), right(lr), cursorX 
	mov		r3, r6, lsr #16			// y
	bic		r6, r6, r3, lsl #16		// x

	add		r0, r4, r3, lsl #2		// dstD= dstBase + y*4
	mov		r3, r6, lsr #3
	mla		r0, ip, r3, r0

	and		r9, r6, #7				// - xshift0 = x&7*4
	mov		r9, r9, lsl #2				// /

	ldrh	r7, [r5, #TTC_ink]

	// [MORE]

	cmp		r11, #8
	// Prep for single-strip render
	suble	sp, sp, #8
	ble		.Lyloop
	// Prep for multi-strip render
	sub		r3, r10, r2
	mov		r10, r0
	stmfd	sp!, {r2, r3}			// Store charH, deltaS
	b		.Lyloop

	// r0	^dstL
	// r1	^srcL
	// r2	^iy*
	// r3	raw			// [TODO] optimize
	// r4	px
	// r5	:pxmask (=15)
	// r6	xstride
	// r7	:ink
	// r8	^xshift
	// r9	:xshift0
	// r10	:dstD
	// r11	^is*
	// ip	:dstP
	// lr				// [TODO] Use?

	// --- Strip loop ---
.Lsloop:
		ldmia	sp, {r2, r3}		@ Reload charH and deltaS
		add		r10, r10, ip		@ (Re)set dstD/dstL
		mov		r0, r10
		add		r1, r1, r3

		// --- Render loop ---
.Lyloop:
			mov		r8, r9		// xshift
			mov		r6, #0		// xstride (rtile offset)
			ldrb	r3, [r1], #1
			cmp		r3, #0
			beq		.LrowDone
.Lxloop:
				tst		r3, #1		// must draw?
				beq		.LpxDone
				cmp		r8, #32		// moving to rtile?
				subge	r8, #32
				addge	r6, ip
				ldr		r4, [r0, r6]
				bic		r4, r5, lsl r8
				orr		r4, r7, lsl r8
				str		r4, [r0, r6]
.LpxDone:
				add		r8, #4
				movs	r3, r3, lsr #1
				bne		.Lxloop

.LrowDone:
			add		r0, #4
			subs	r2, #1
			bne		.Lyloop

		// Test for strip loop
		subs	r11, #8
		bgt		.Lsloop
	
	add		sp, sp, #8
	ldmfd	sp!, {r4-r11, lr}
	bx		lr
END_FUNC(chr4c_drawg_b1cts_asm_base_arm_iwram)


// EOF
