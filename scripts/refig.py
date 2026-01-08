from dataclasses import dataclass
import json
from pathlib import Path
import os
import re
import textwrap


def reindent(text:str, width:int, nesting:int, neststr:str = '\t'):

	indent = neststr * nesting

	text = text = re.sub(r'\s+', ' ', text).strip()
	text = textwrap.fill(text, 
		width=width, 
		break_long_words=False, 
		break_on_hyphens=False,
		initial_indent=indent,
		subsequent_indent=indent,
		replace_whitespace=True,
		drop_whitespace=True,
	)
	return text

class Figure:
	"""
	Model of a figure.
	"""
	REX_MAIN:str = r'(<div\b[^>]*\bclass="(?P<cls>cpt(_fl|_fr)?)"[^>]*>(?P<data>.*?)</div>)'
	REX_SUB:str = r'(?P<cnt><(?P<tag>\w+)\s*[^>]*>(.*?</\2>)?)(?P<cap>.*$)'

	match:re.Match	##< Regexp match.
	text:str		##< The entire html of the figure.
	cls:str			##< Figure class.
	content:str		##< Main content of the figure.
	caption:str		##< Caption part of the figure.
	tag:str			##< Main tag.

	def __init__(self, m:re.Match):
		self.match = m
		self.text = m[0]
		self.cls = m['cls']
		data = m['data'].strip()

		rex = re.compile(Figure.REX_SUB, re.DOTALL)
		m = rex.search(data)
		self.tag = m['tag']
		self.content = m['cnt'].strip()
		self.caption = m['cap'].strip()
		if self.caption.startswith('<br>'):
			self.caption = self.caption[4:].strip()

		if self.tag == 'table':
			pass

		pass

	def sub(self):
		indent = '  ' * 2
		caption = reindent(self.caption, 96, 2, '  ')

		repl:str = f"""
<figure class="{self.cls}">
  <div>
    {self.content}
  </div>
  <figcaption>
{caption}
  </figcaption>
</figure>
"""
		return repl.strip()

@dataclass(slots=True)
class Refig:
	text: str
	figures: list[str]

	def __init__(self, text: str):
		self.text: str = text
		self.figures: list[str] = []

	def find_figures(self) -> list[str]:
		"""
		Finds all elements with `class="cpt|cpt_fl|cpt_fr"` in the text and stores them in self.figures
		"""
		rex = re.compile(Figure.REX_MAIN, re.DOTALL)
		self.figures = [Figure(m) for m in rex.finditer(self.text) ]
		return self.figures
	
	def sub(self) -> str:
		"""
		Makes a string with substitutions.
		"""
		if len(self.figures) == 0:
			return self.text
		
		parts = [ self.text[:self.figures[0].match.start()] ]
		parts.append(self.figures[0].sub())
		for i in range(1, len(self.figures)):
			parts.append(self.text[self.figures[i-1].match.end():self.figures[i].match.start()])
			parts.append(self.figures[i].sub())
		parts.append(self.text[self.figures[-1].match.end():])

		text = ''.join(parts)
		return text

def test():
	str = """
abcd
<div class="cpt_fr" style="width:216px;">
  <img src="../img/bitmaps/pageflip.png" id="img-flip" 
    alt="Page flipping procedure"><br>
  <b>Fig <em>[[ref:img-flip]]</em></b>: Page flipping procedure. 
  No data is copied, only the &lsquo;display&rsquo; and 
  &lsquo;write&rsquo; pointers are swapped.
</div>
two
  <div class="cpt" style="width:310px">
  <img src="../img/bitmaps/link_lttp.png"
    alt="zoom out of Fig 1">
    <b>Fig <em>[[ref:img-link-big]]</em>a</b>: zoom out of 
    fig&nbsp;<em>[[ref:img-link-sm]]</em>, with pixel offsets.
  </div>
efgh
"""
	refig = Refig(str)
	refig.find_figures()
	
	print(str)
	for i, fig in enumerate(refig.figures):
		print(f"{fig.sub()}\n")
	out = refig.sub()

	print(out)

# ----------------------
# Example usage
# ----------------------
if __name__ == "__main__":
	#test()
	#exit()
	with open('config.json', 'r') as f:
		config = json.load(f)["autoref"]

	dst_dir = '../extra/out/'
	types:dict[str,int] = {}

	for el in config['files']:
		path = os.path.join(config['srcdir'], el['fname'])

		#path:str = "../prehtml/bitmaps.htm"
		# Load a file
		text:str = Path(path).read_text(encoding="utf-8")
		refig = Refig(text)
		refig.find_figures()

		print(f"{path} : {len(refig.figures)}")
		if len(refig.figures) == 0:
			continue

		text = refig.sub()
		path = os.path.join(dst_dir, el['fname'])
		Path(path).write_text(text, encoding="utf-8")		
		
		# for i, fig in enumerate(refig.figures):
		# 	print(f"  {fig.cls}\t{fig.tag}\t{fig.match.start()}-{fig.match.end()}")

		# 	#print(f"  {fig.cls}\t{fig.tag}\t{fig.caption}")
		# 	print(f"{fig.sub()}\n")

		# 	types[fig.tag] = 1 if fig.tag not in types else types[fig.tag]+1

	print('\nSummary:')
	for k,v in types.items():
		print(f"  {k}\t{v}")