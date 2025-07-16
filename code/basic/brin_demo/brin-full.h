
//{{BLOCK(brin_full)

//======================================================================
//
//	brin_full, 512x256@8, 
//	+ palette 256 entries, not compressed
//	+ 31 tiles (t|f|p reduced) lz77 compressed
//	+ regular map (flat), lz77 compressed, 32x16 
//	Metatiled by 2x2
//	Total size: 512 + 916 + 120 + 1024 = 2572
//
//	Time-stamp: 2015-10-04, 16:53:56
//	Exported by Cearn's GBA Image Transmogrifier, v0.8.3
//	( http://www.coranac.com/projects/#grit )
//
//======================================================================

#ifndef GRIT_BRIN_FULL_H
#define GRIT_BRIN_FULL_H

#define brin_fullTilesLen 916
extern const unsigned short brin_fullTiles[458];

#define brin_fullMetaTilesLen 120
extern const unsigned short brin_fullMetaTiles[60];

#define brin_fullMetaMapLen 1024
extern const unsigned short brin_fullMetaMap[512];

#define brin_fullPalLen 512
extern const unsigned short brin_fullPal[256];

#endif // GRIT_BRIN_FULL_H

//}}BLOCK(brin_full)
