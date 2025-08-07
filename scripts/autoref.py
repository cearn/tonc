
import os
from pprint import pprint
import re
import json
from bs4 import BeautifulSoup

class AutoReffer:
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
		self.prefix_rules = {}
		self.srcdir = ""
		self.dstdir = ""
		self.files = []

		# internals
		self.current_ch = None
		self.ch_type = None

		# results
		self.results = {}		# fname:FileInfo map

		self._init_reftype_rules()
		self._load_config()

	# --- Chapter Helpers ---
	def _roman_to_int(self, roman):
		roman = roman.lower()
		val = {'i': 1, 'v': 5, 'x': 10, 'l': 50,
			'c': 100, 'd': 500, 'm': 1000}

		total = 0
		prev = 0
		for ch in reversed(roman):
			curr = val[ch]
			total += curr if curr >= prev else -curr
			prev = curr
		return total

	def _int_to_roman(self, num):
		val = [
			(1000, "m"), (900, "cm"), (500, "d"),
			(400, "cd"), (100, "c"), (90, "xc"),
			(50, "l"), (40, "xl"), (10, "x"),
			(9, "ix"), (5, "v"), (4, "iv"), (1, "i")
		]

		result = ""
		for (v, symbol) in val:
			while num >= v:
				result += symbol
				num -= v
		return result.lower()

	def _detect_ch_type(self, ch):
		if ch == "i":		return "roman"
		elif ch.isupper():	return "upper"
		elif ch.islower():	return "lower"
		else:				return "number"

	def _increment_ch(self):
		if self.ch_type == "number":
			self.current_ch = str(int(self.current_ch) + 1)
		elif self.ch_type == "roman":
			self.current_ch = self._int_to_roman(self._roman_to_int(self.current_ch) + 1)
		elif self.ch_type == "upper":
			self.current_ch = chr(ord(self.current_ch) + 1)
		elif self.ch_type == "lower":
			self.current_ch = chr(ord(self.current_ch) + 1)

	def _load_config(self):
		with open(self.config_path, "r") as f:
			config = json.load(f)["autoref"]

		self.files = config["files"]
		self.srcdir = config["srcdir"]
		self.dstdir = config["dstdir"]

	# --- Reftype stuf ---
	#{{
	def _init_reftype_rules(self):
		"""
		Formatting and updating rules for the reftypes.
		"""
		self.prefix_.rules = {
			"ch":   {"fmt": "{ch}.",              "update": self._reftype_update_none},
			"sec":  {"fmt": "{ch}.{sec}.",        "update": self._reftype_update_sec},
			"ssec": {"fmt": "{ch}.{sec}.{ssec}.", "update": self._reftype_update_ssec},
			"eq":   {"fmt": "{ch}.{eq}",          "update": self._reftype_update_simple("eq")},
			"img":  {"fmt": "{ch}.{img}",         "update": self._reftype_update_simple("img")},
			"tbl":  {"fmt": "{ch}.{tbl}",         "update": self._reftype_update_simple("tbl")},
			"cd":   {"fmt": "{ch}.{cd}",          "update": self._reftype_update_simple("cd")},
		}

	def _reftype_update_none(self, key):
		pass

	def _reftype_update_simple(self, key):
		def updater(counters):
			counters[key] += 1
		return updater

	def _reftype_update_sec(self, counters):
		counters["sec"] += 1
		counters["ssec"] = 0

	def _reftype_update_ssec(self, counters):
		counters["ssec"] += 1
	#}}


	def _single_run(self, fname, counters):
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

		print(f"\n--- {fname} (ch={self.current_ch}) ---")
		with open(path, "r", encoding="utf-8") as fin:
			content = fin.read()

		# Find ids & labels
		soup = BeautifulSoup(content, "html.parser")
		results = self._single_find_info(soup, counters)
		self.results[fname] = results

		# Replace refs 
		content = self._single_update_refs(content, results.labels)
		# Update TOC
		content = self._single_update_toc(content, results.sections)

		# --- Save ---
		path = os.path.join(self.dstdir, fname)
		with open(path, "w", encoding="utf-8") as fout:
			fout.write(content)

		pass

	def _single_find_info(self, soup:BeautifulSoup, counters:dict):
		"""
		Collects info for later processing.
		@returns FileInfo object 
		"""
		finfo = self.FileInfo();				# results
		rex = re.compile(r'\[\[ref:(.+?)\]\]') 	# for cleaning the title

		# --- Find autonum IDs ---
		for tag in soup.find_all(id=True):
			id = tag["id"]
			if "-" not in id:
				continue
			prefix, _ = id.split("-", 1)
			if prefix not in self.prefix_rules:
				continue

			rule = self.prefix_rules[prefix]
			rule["update"](counters)
			label = rule["fmt"].format(**counters)
			finfo.labels[id] = label

			if prefix == "sec":
				title = rex.sub("", tag.text)
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

	# --- Main Runner ---
	def run(self):
		for entry in self.files:
			if entry.get("ignore"):
				continue

			# Chapter number management
			if "ch" in entry:
				self.current_ch = entry["ch"]
				self.ch_type = self._detect_ch_type(self.current_ch)
			elif self.current_ch:
				self._increment_ch()
			else:
				self.current_ch = 1
				self.ch_type = "number"

			# Reset counters for this file
			counters = {k: 0 for k in self.prefix_rules}
			counters['ch'] = self.current_ch
			self._single_run(entry["fname"], counters)


if (__name__ == "__main__"):
	processor = AutoReffer("config.json")
	processor.run()
 