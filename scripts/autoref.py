
import os
import re
import json
import roman
from bs4 import BeautifulSoup

from pprint import pprint

class AutoReffer:
	class RefType:
		def __init__(self, group:dict, name:str, format:str, 
			resets:list[str] = [], style:str = 'n', value:int = 0):
			"""
			Constructs a new RefType object. Starts counting at 1, or dflt if that's set.
			@param group	Dict of str->RefTypes that this object belongs to.
			@param name		Name of RefType.
			@param format	Formats string for RefType. E.g.: "{ch}.{eq}"
			@param resets	RefTypes that should be reset to 0 when this is updated.
			@param style	Style for the string of this RefType. Options:
							- 'n': numeric.
							- 'A': Uppercase letters.
							- 'a': Lowercasse letters.
							- 'I': Uppercase Roman numerals.
							- 'i': Lowercase Roman numerals.
			@param value	The initial value.
			@note	The value is updated when a new item is found. So if @a value = 0, 
					the first item will actually be 1.
			"""
			self._group = group
			self._name = name
			self._format = format
			self._resets = resets

			self._numstyle = style
			self._value = value
			self._svalue = ""
			
		def __str__(self):
			return self._svalue
			
		def update(self):
			self._group[self._name].inc()
			[ self._group[k].set(0) for k in self._resets]
			
		def label(self) -> str:
			return self._format.format(**self._group)

		def inc(self):
			self.set(self._value+1)
		
		def set(self, value: int, bnext:bool = False):
			"""
			@param value 	Value to use now.
			@param bnext	Use the value for the _next_ item found. Usually, the value is 
							incremented then. So if @a value = 2, the next item will actually 
							be 3, which may not be what you want. Use `bnext = True` to 
							correct for this.
			"""
			if bnext == True:
				value -= 1
			self._value = value
			self._cache_str()
			
		def get(self) -> int:
			return self._value
		
		def set_style(self, numstyle:str):
			self._numstyle = numstyle
			self._cache_str()

		def _cache_str(self):
			style = self._numstyle
			v = self._value

			if   style == 'n': svalue = str(v)
			elif style == 'A': svalue = chr(ord('A') + v-1)
			elif style == 'a': svalue = chr(ord('a') + v-1)
			elif style == 'R': svalue = roman.toRoman(v)
			elif style == 'r': svalue = roman.toRoman(v).lower()
			else: 
				print(f'WARNING: unknown style for `{self._name}`: "{style}"')
				svalue = str(v)

			self._svalue = svalue

	class FileInfo:
		"""
		Analysis results for a single source file.
		"""
		def __init__(self):
			self.labels = {}	# id:label map
			self.sections = {}	# id:sec-string map


	def __init__(self, config_path):
		self.config_path = config_path
		# config
		self.srcdir:str = ""
		self.dstdir:str = ""
		self.files:list[str] = []

		#internals
		self._reftypes:dict[str, AutoReffer.RefType] = {}
		self.results:dict[str,AutoReffer.FileInfo] = {}

		self._load_config()
		self._init_reftypes()

	def _load_config(self):
		with open(self.config_path, 'r') as f:
			config = json.load(f)["autoref"]

		self.srcdir = config['srcdir']
		self.dstdir = config['dstdir']
		self.files = config['files']

	def _init_reftypes(self):
		"""
		Formatting and updating rules for the reftypes.
		"""

		reftypes = {}
		reftypes['ch']  = self.RefType(reftypes, 'ch',   '{ch}.')
		reftypes['sec'] = self.RefType(reftypes, 'sec',  '{ch}.{sec}.', resets = ['ssec'])
		reftypes['ssec'] = self.RefType(reftypes, 'ssec', '{ch}.{sec}.{ssec}.')
		reftypes['eq'] =  self.RefType(reftypes, 'eq',   '{ch}.{eq}')
		reftypes['img']=  self.RefType(reftypes, 'img',  '{ch}.{img}')
		reftypes['tbl']=  self.RefType(reftypes, 'tbl',  '{ch}.{tbl}')
		reftypes['cd']=   self.RefType(reftypes, 'cd',   '{ch}.{cd}')
		self._reftypes = reftypes

	# --- Main Runner ---
	def run(self):
		for entry in self.files:
			if entry.get('ignore'):
				continue

			# [TODO] Resetting everything here is a hack. Ideally, we can just
			# reset everything on a new 'ch'. We have functionality for that now.
			ch = self._reftypes['ch']
			self._init_reftypes()

			if 'ch' in entry and len(entry['ch']) > 0:
				style = entry['ch'][:1]
				value = entry['ch'][1:]
				value = int(value) if len(value) > 0 else 1
				ch.set(int(value), True)
				ch.set_style(style)

			self._reftypes['ch'] = ch

			self._single_run(entry['fname'])

	def _single_run(self, fname):
		"""
		Processes a single file. 
		- Gathers the IDs and their labels.
		- Updates the references.
		- Updates its Table of Contents.
		- Writes to {dstdir}/{fname}
		"""
		path = os.path.join(self.srcdir, fname)
		if not os.path.isfile(path):
			print(f"[!] Skipping missing file: {fname}")
			return

		print(f"\n--- {fname} (ch={self._reftypes['ch']}) ---")
		with open(path, 'r', encoding='utf-8') as fin:
			content = fin.read()

		# Find ids & labels
		soup = BeautifulSoup(content, "html.parser")
		results = self._single_find_info(soup)
		self.results[fname] = results

		# Replace refs 
		content = self._single_update_refs(content, results.labels)
		# Update TOC
		content = self._single_update_toc(content, results.sections)

		# --- Save ---
		path = os.path.join(self.dstdir, fname)
		with open(path, 'w', encoding='utf-8') as fout:
			fout.write(content)

		pass

	def _single_find_info(self, soup:BeautifulSoup) -> FileInfo:
		"""
		Collects info for later processing.
		@returns FileInfo object 
		"""
		finfo = self.FileInfo();				# results
		rex = re.compile(r'<em>\[\[ref:(.+?)\]\]</em>') 	# for cleaning the title

		# --- Find autonum IDs ---
		for tag in soup.find_all(id=True):
			id = tag['id']
			if "-" not in id:
				continue
			reftype, _ = id.split('-', 1)
			if reftype not in self._reftypes:
				continue

			rule = self._reftypes[reftype]
			rule.update()
			label = rule.label()
			finfo.labels[id] = label

			if reftype == 'sec':
				# Track sections for ToC
				# Note: BS4 converts htmlentities, so we have to convert them back.
				# This has to be done in a convoluted way. This one 'works', but 
				# returns numeric ones. For named ones, see `html.entities`?
				title = tag.decode_contents().encode('ascii', 'xmlcharrefreplace').decode('ascii')
				title = rex.sub("", title)
				title = title.strip().replace('\n', '')
				finfo.sections[id] = title
				print(f"{id} -> {label} ({title})")
			else:
				print(f"{id} -> {label}")

		return finfo

	def _single_update_refs(self, content:str, labels:dict):
		rex = re.compile(r'<em>\[\[ref:(.+?)\]\]</em>')

		def repl(match):
			ref_id = match.group(1)
			if ref_id in labels:
				return labels[ref_id]
			else:
				print(f"Error: unknown reference id '{ref_id}'")
				return match.group(0)
		return rex.sub(repl, content)
	
	def _single_update_toc(self, content, sections:dict):
		# Dammit, I need both the ID and text for this, but also without the ref. 
		# Need to think about this more.
		if len(sections) == 0: return content

		toc = '\n'.join([ f'  <li><a href="#{k}">{v}</a></li>' for k,v in sections.items()])
		toc = f"""
<ul>
{toc}
</ul>
"""
		rex = re.compile(r'(?<=<!-- \[\[toc\]\] -->)(.*?)(?=<!-- \[\[/toc\]\] -->)', flags=re.DOTALL)
		content = rex.sub(toc, content)

		return content


if (__name__ == "__main__"):
	processor = AutoReffer("config.json")
	processor.run()
