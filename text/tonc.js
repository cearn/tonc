//
// \file tonc.js
// \author cearn
// \date 20060505-20060505
// === NOTES ===
//

// Resolve MSIE CSS2 dumbness
if(navigator.appName.indexOf('Microsoft') >= 0)
	document('<'+'link rel="stylesheet" type="text/css" href="ie.css" />');


function main()
{
	id2title();
	deprecationNotice();
}

//! Add an appropriate title-attr to main tags with ids.
function id2title()
{
	let ii, jj, tags, id;
	const tagnames= ["div", "h1", "h2", "h3", "img", "pre", "table"];

	for(ii in tagnames)
	{
		tags= document.getElementsByTagName(tagnames[ii]);
		for(jj in tags)
		{
			if(tags[jj].id && tags[jj].title=="")
				tags[jj].title= tags[jj].id;
		}
	}
}

function deprecationNotice()
{
	const url = "https://gbadev.net/tonc/";

	let banner = document.createElement("div");
	banner.className = "banner-deprecation";
	banner.innerHTML = `<span>
	  NOTICE: Tonc is no longer actively maintained here. 
		For an up-to-date version, go to <a href="${url}">${url}</a>
		</span>`;

		document.body.insertBefore(banner, document.body.firstChild);
}