//
// bm_modes.c
// Combined demo of modes 3, 4 and 5
//
// (20031002 - 20251227, cearn)

#include <string.h>
#include "toolbox.h"

#include "modes.h"

int main()
{
	int mode= 3;
	REG_DISPCNT= mode | DCNT_BG2;

	// Set this to 0 for the original demo.
#if 1
	memcpy32(vid_mem, modesBitmap, modesBitmapLen/4);
	memcpy32(pal_bg_mem, modesPal, modesPalLen/4);
#else
	memcpy(vid_mem, modesBitmap, modesBitmapLen);
	memcpy(pal_bg_mem, modesPal, modesPalLen);
#endif

	while(1)
	{
		// Wait till VBlank before doing anything
		vid_vsync();

		// Check keys for mode change
		key_poll();
		if(key_hit(KEY_LEFT) && mode>3)
			mode--;
		else if(key_hit(KEY_RIGHT) && mode<5)
			mode++;

		// Change the mode
		REG_DISPCNT= mode | DCNT_BG2;
	}

	return 0;
}
