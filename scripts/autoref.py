
import os
import re
import json
from bs4 import BeautifulSoup

class AutoReffer:
	def __init__(self, config_path):
		self.config_path = config_path
		self.prefix_rules = {}
		self.files = []
		self.srcdir = ""
		self.current_ch = None
		self.ch_type = None

		self.id_map = {}

		self.setup_prefix_rules()
		self.load_config()

	# --- Chapter Helpers ---
	def roman_to_int(self, roman):
		roman = roman.lower()
		val = {'I': 1, 'V': 5, 'X': 10, 'L': 50,
				'C': 100, 'D': 500, 'M': 1000}
		val = {'i': 1, 'v': 5, 'x': 10, 'l': 50,
			'c': 100, 'd': 500, 'm': 1000}

		total = 0
		prev = 0
		for ch in reversed(roman):
			curr = val[ch]
			total += curr if curr >= prev else -curr
			prev = curr
		return total

	def int_to_roman(self, num):
		val = [
			(1000, "M"), (900, "CM"), (500, "D"),
			(400, "CD"), (100, "C"), (90, "XC"),
			(50, "L"), (40, "XL"), (10, "X"),
			(9, "IX"), (5, "V"), (4, "IV"), (1, "I")
		]
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

	def detect_ch_type(self, ch):
		if ch == "i":		return "roman"
		elif ch.isupper():	return "upper"
		elif ch.islower():	return "lower"
		else:				return "number"

	def increment_ch(self):
		if self.ch_type == "number":
			self.current_ch = str(int(self.current_ch) + 1)
		elif self.ch_type == "roman":
			self.current_ch = self.int_to_roman(self.roman_to_int(self.current_ch) + 1)
		elif self.ch_type == "upper":
			self.current_ch = chr(ord(self.current_ch) + 1)
		elif self.ch_type == "lower":
			self.current_ch = chr(ord(self.current_ch) + 1)

	# --- Prefix Rules -
	def update_none(self, key):
		pass

	def update_simple(self, key):
		def updater(counters):
			counters[key] += 1
		return updater

	def update_sec(self, counters):
		counters["sec"] += 1
		counters["ssec"] = 0

	def update_ssec(self, counters):
		counters["ssec"] += 1

	def setup_prefix_rules(self):
		self.prefix_rules = {
			"ch":   {"fmt": "{ch}.",              "update": self.update_none},
			"sec":  {"fmt": "{ch}.{sec}.",        "update": self.update_sec},
			"ssec": {"fmt": "{ch}.{sec}.{ssec}.", "update": self.update_ssec},
			"eq":   {"fmt": "{ch}.{eq}",          "update": self.update_simple("eq")},
			"img":  {"fmt": "{ch}.{img}",         "update": self.update_simple("img")},
			"tbl":  {"fmt": "{ch}.{tbl}",         "update": self.update_simple("tbl")},
			"cd":   {"fmt": "{ch}.{cd}",          "update": self.update_simple("cd")},
		}

	# --- Config Loading ---
	def load_config(self):
		with open(self.config_path, "r") as f:
			config = json.load(f)["autoref"]
		self.files = config["files"]
		self.srcdir = config["srcdir"]
		self.dstdir = config["dstdir"]

	# --- File Processing ---

	def process_file(self, fname, counters):
		path = os.path.join(self.srcdir, fname)
		if not os.path.isfile(path):
			print(f"[!] Skipping missing file: {fname}")
			return

		with open(path, "r", encoding="utf-8") as fin:
			content = fin.read()

		print(f"\n--- {fname} (ch={self.current_ch}) ---")

		# --- Find autonum IDs ---
		soup = BeautifulSoup(content, "html.parser")
		self.id_map[fname] = {}
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
			self.id_map[fname][id] = label

			print(f"{id} -> {label}")

		# --- Replace refs ---
		labels = self.id_map[fname]
		pattern = re.compile(r'<em>\[\[ref:(.+?)\]\]</em>')

		def repl(match):
			ref_id = match.group(1)
			if ref_id in labels:
				return labels[ref_id]
			else:
				print(f"Error: unknown reference id '{ref_id}'")
				return match.group(0)
		content = pattern.sub(repl, content)

		path = os.path.join(self.dstdir, fname)
		with open(path, "w", encoding="utf-8") as fout:
			fout.write(content)

		"""
		ref_pattern = re.compile(r'^\[\[ref:(.+?)\]\]$')
		for em in soup.find_all("em"):
			if em.string:
				match = ref_pattern.match(em.string.strip())
				if match:
					ref_id = match.group(1)
					if ref_id in labels:
						em.replace_with(labels[ref_id])
					else:
						print(f"Error: unknown reference id '{ref_id}'")
		
		# --- Write to dst ---
		path = os.path.join(self.dstdir, fname)
		with open(path, "w", encoding="utf-8") as fout:
			fout.write(str(soup))
		"""

		pass

	# --- Main Runner ---
	def run(self):
		for entry in self.files:
			if entry.get("ignore"):
				continue

			# Chapter number management
			if "ch" in entry:
				self.current_ch = entry["ch"]
				self.ch_type = self.detect_ch_type(self.current_ch)
			elif self.current_ch:
				self.increment_ch()
			else:
				self.current_ch = 1
				self.ch_type = "number"

			# Reset counters for this file
			counters = {k: 0 for k in self.prefix_rules}
			counters['ch'] = self.current_ch
			self.process_file(entry["fname"], counters)

			# [TODO] replace refs

if (__name__ == "__main__"):
	processor = AutoReffer("config.json")
	processor.run()
 