
import os
from pprint import pprint
import re
import json
from bs4 import BeautifulSoup

class AutoReffer:
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
		self.id_map = {}		# fname -> { id : label }
		self.sections = {}		# fname -> { sec_id : sec_title }

		self._setup_prefix_rules()
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

	# --- Prefix Rules ---
	def _update_none(self, key):
		pass

	def _update_simple(self, key):
		def updater(counters):
			counters[key] += 1
		return updater

	def _update_sec(self, counters):
		counters["sec"] += 1
		counters["ssec"] = 0

	def _update_ssec(self, counters):
		counters["ssec"] += 1

	def _setup_prefix_rules(self):
		self.prefix_rules = {
			"ch":   {"fmt": "{ch}.",              "update": self._update_none},
			"sec":  {"fmt": "{ch}.{sec}.",        "update": self._update_sec},
			"ssec": {"fmt": "{ch}.{sec}.{ssec}.", "update": self._update_ssec},
			"eq":   {"fmt": "{ch}.{eq}",          "update": self._update_simple("eq")},
			"img":  {"fmt": "{ch}.{img}",         "update": self._update_simple("img")},
			"tbl":  {"fmt": "{ch}.{tbl}",         "update": self._update_simple("tbl")},
			"cd":   {"fmt": "{ch}.{cd}",          "update": self._update_simple("cd")},
		}

	# --- Config Loading ---
	def _load_config(self):
		with open(self.config_path, "r") as f:
			config = json.load(f)["autoref"]
		self.files = config["files"]
		self.srcdir = config["srcdir"]
		self.dstdir = config["dstdir"]

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
		self.id_map[fname] = self._single_find_labels(soup, counters)
		# Replace refs 
		content = self._single_update_refs(content, self.id_map[fname])
		# Update TOC
		content = self._single_update_toc(content, self.id_map[fname])

		# --- Save ---
		path = os.path.join(self.dstdir, fname)
		with open(path, "w", encoding="utf-8") as fout:
			fout.write(content)

		pass

	def _single_find_labels(self, soup:BeautifulSoup, counters:dict):
		labels = {}
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
			labels[id] = label

			print(f"{id} -> {label}")
		return labels
	
	def _single_find_sections(self, soup:BeautifulSoup):
		pass

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
	
	def _single_update_toc(self, content, labels:dict):
		return content
	
		# Dammit, I need both the ID and text for this, but also without the ref. 
		# Need to think about this more.
		secs = { k:v for k,v in labels.items() if k.startswith('sec') }
		if len(secs): return content

		# find full <h2 id=""></h2> things.


		rex = re.compile(r'(?<=<!-- \[\[toc\]\] -->)(.*?)(?=<!-- \[\[/toc\]\] -->)', flags=re.DOTALL)
		match = rex.findall(content)

		pprint(match)
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

			# [TODO] replace refs

if (__name__ == "__main__"):
	processor = AutoReffer("config.json")
	processor.run()
 