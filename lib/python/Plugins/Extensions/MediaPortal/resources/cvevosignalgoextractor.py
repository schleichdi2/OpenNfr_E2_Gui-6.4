# -*- coding: utf-8 -*-
# This code is based on youtube-dl: https://github.com/rg3/youtube-dl

from __future__ import unicode_literals

import json
import operator
import os
import sys
import re
import requests

_NO_DEFAULT = object()
compat_chr = unichr
compat_str = unicode
exception_err = lambda e: "%s\n%s\n" % (type(e), "".join(e.args))

class ExceptionTemplate(Exception):
	def __call__(self, *args):
		return self.__class__(*(self.args + args))
	def __str__(self):
		return ': '.join(self.args)
class ExtractorError(ExceptionTemplate): pass
extractorError = ExtractorError('JSInterpreter: ')


_OPERATORS = [
	('|', operator.or_),
	('^', operator.xor),
	('&', operator.and_),
	('>>', operator.rshift),
	('<<', operator.lshift),
	('-', operator.sub),
	('+', operator.add),
	('%', operator.mod),
	('/', operator.truediv),
	('*', operator.mul),
]
_ASSIGN_OPERATORS = [(op + '=', opfunc) for op, opfunc in _OPERATORS]
_ASSIGN_OPERATORS.append(('=', lambda cur, right: right))

_NAME_RE = r'[a-zA-Z_$][a-zA-Z_$0-9]*'

compiled_regex_type = type(re.compile(''))

class JSInterpreter(object):
	def __init__(self, code, objects=None):
		if objects is None:
			objects = {}
		self.code = code
		self._functions = {}
		self._objects = objects

	def interpret_statement(self, stmt, local_vars, allow_recursion=100):
		if allow_recursion < 0:
			raise extractorError('Recursion limit reached')

		should_abort = False
		stmt = stmt.lstrip()
		stmt_m = re.match(r'var\s', stmt)
		if stmt_m:
			expr = stmt[len(stmt_m.group(0)):]
		else:
			return_m = re.match(r'return(?:\s+|$)', stmt)
			if return_m:
				expr = stmt[len(return_m.group(0)):]
				should_abort = True
			else:
				# Try interpreting it as an expression
				expr = stmt

		v = self.interpret_expression(expr, local_vars, allow_recursion)
		return v, should_abort

	def interpret_expression(self, expr, local_vars, allow_recursion):
		expr = expr.strip()

		if expr == '':  # Empty expression
			return None

		if expr.startswith('('):
			parens_count = 0
			for m in re.finditer(r'[()]', expr):
				if m.group(0) == '(':
					parens_count += 1
				else:
					parens_count -= 1
					if parens_count == 0:
						sub_expr = expr[1:m.start()]
						sub_result = self.interpret_expression(
							sub_expr, local_vars, allow_recursion)
						remaining_expr = expr[m.end():].strip()
						if not remaining_expr:
							return sub_result
						else:
							expr = json.dumps(sub_result) + remaining_expr
						break
			else:
				raise extractorError('Premature end of parens in %r' % expr)

		for op, opfunc in _ASSIGN_OPERATORS:
			m = re.match(r'''(?x)
				(?P<out>%s)(?:\[(?P<index>[^\]]+?)\])?
				\s*%s
				(?P<expr>.*)$''' % (_NAME_RE, re.escape(op)), expr)
			if not m:
				continue
			right_val = self.interpret_expression(
				m.group('expr'), local_vars, allow_recursion - 1)

			if m.groupdict().get('index'):
				lvar = local_vars[m.group('out')]
				idx = self.interpret_expression(
					m.group('index'), local_vars, allow_recursion)
				assert isinstance(idx, int)
				cur = lvar[idx]
				val = opfunc(cur, right_val)
				lvar[idx] = val
				return val
			else:
				cur = local_vars.get(m.group('out'))
				val = opfunc(cur, right_val)
				local_vars[m.group('out')] = val
				return val

		if expr.isdigit():
			return int(expr)

		var_m = re.match(
			r'(?!if|return|true|false)(?P<name>%s)$' % _NAME_RE,
			expr)
		if var_m:
			return local_vars[var_m.group('name')]

		try:
			return json.loads(expr)
		except ValueError:
			pass

		m = re.match(
			r'(?P<var>%s)\.(?P<member>[^(]+)(?:\(+(?P<args>[^()]*)\))?$' % _NAME_RE,
			expr)
		if m:
			variable = m.group('var')
			member = m.group('member')
			arg_str = m.group('args')

			if variable in local_vars:
				obj = local_vars[variable]
			else:
				if variable not in self._objects:
					self._objects[variable] = self.extract_object(variable)
				obj = self._objects[variable]

			if arg_str is None:
				# Member access
				if member == 'length':
					return len(obj)
				return obj[member]

			assert expr.endswith(')')
			# Function call
			if arg_str == '':
				argvals = tuple()
			else:
				argvals = tuple([
					self.interpret_expression(v, local_vars, allow_recursion)
					for v in arg_str.split(',')])

			if member == 'split':
				assert argvals == ('',)
				return list(obj)
			if member == 'join':
				assert len(argvals) == 1
				return argvals[0].join(obj)
			if member == 'reverse':
				assert len(argvals) == 0
				obj.reverse()
				return obj
			if member == 'slice':
				assert len(argvals) == 1
				return obj[argvals[0]:]
			if member == 'splice':
				assert isinstance(obj, list)
				index, howMany = argvals
				res = []
				for i in range(index, min(index + howMany, len(obj))):
					res.append(obj.pop(index))
				return res

			return obj[member](argvals)

		m = re.match(
			r'(?P<in>%s)\[(?P<idx>.+)\]$' % _NAME_RE, expr)
		if m:
			val = local_vars[m.group('in')]
			idx = self.interpret_expression(
				m.group('idx'), local_vars, allow_recursion - 1)
			return val[idx]

		for op, opfunc in _OPERATORS:
			m = re.match(r'(?P<x>.+?)%s(?P<y>.+)' % re.escape(op), expr)
			if not m:
				continue
			x, abort = self.interpret_statement(
				m.group('x'), local_vars, allow_recursion - 1)
			if abort:
				raise extractorError(
					'Premature left-side return of %s in %r' % (op, expr))
			y, abort = self.interpret_statement(
				m.group('y'), local_vars, allow_recursion - 1)
			if abort:
				raise extractorError(
					'Premature right-side return of %s in %r' % (op, expr))
			return opfunc(x, y)

		m = re.match(
			r'^(?P<func>%s)\((?P<args>[a-zA-Z0-9_$,]*)\)$' % _NAME_RE, expr)
		if m:
			fname = m.group('func')
			argvals = tuple([
				int(v) if v.isdigit() else local_vars[v]
				for v in m.group('args').split(',')]) if len(m.group('args')) > 0 else tuple()
			if fname not in self._functions:
				self._functions[fname] = self.extract_function(fname)
			return self._functions[fname](argvals)

		raise extractorError('Unsupported JS expression %r' % expr)

	def extract_object(self, objname):
		obj = {}
		obj_m = re.search(
			(r'(?:var\s+)?%s\s*=\s*\{' % re.escape(objname)) +
			r'\s*(?P<fields>([a-zA-Z$0-9]+\s*:\s*function\(.*?\)\s*\{.*?\}(?:,\s*)?)*)' +
			r'\}\s*;',
			self.code)
		fields = obj_m.group('fields')
		# Currently, it only supports function definitions
		fields_m = re.finditer(
			r'(?P<key>[a-zA-Z$0-9]+)\s*:\s*function'
			r'\((?P<args>[a-z,]+)\){(?P<code>[^}]+)}',
			fields)
		for f in fields_m:
			argnames = f.group('args').split(',')
			obj[f.group('key')] = self.build_function(argnames, f.group('code'))

		return obj

	def extract_function(self, funcname):
		func_m = re.search(
			r'''(?x)
				(?:function\s+%s|[{;,]\s*%s\s*=\s*function|var\s+%s\s*=\s*function)\s*
				\((?P<args>[^)]*)\)\s*
				\{(?P<code>[^}]+)\}''' % (
				re.escape(funcname), re.escape(funcname), re.escape(funcname)),
			self.code)
		if func_m is None:
			raise extractorError('Could not find JS function %r' % funcname)
		argnames = func_m.group('args').split(',')

		return self.build_function(argnames, func_m.group('code'))

	def call_function(self, funcname, *args):
		f = self.extract_function(funcname)
		return f(args)

	def build_function(self, argnames, code):
		def resf(args):
			local_vars = dict(zip(argnames, args))
			for stmt in code.split(';'):
				res, abort = self.interpret_statement(stmt, local_vars)
				if abort:
					break
			return res
		return resf

class CVevoSignAlgoExtractor:
	# MAX RECURSION Depth for security
	MAX_REC_DEPTH = 5

	def __init__(self):
		self._player_cache = {}
		self._cleanTmpVariables()

	def _cleanTmpVariables(self):
		self.playerData = ''

	def decryptSignature(self, s, playerUrl):
		if not playerUrl.startswith('http'):
			playerUrl = "https://www.youtube.com" + playerUrl
		# clear local data
		self._cleanTmpVariables()

		id_m = re.match(
			r'.*?-(?P<id>[a-zA-Z0-9_-]+)(?:/watch_as3|/html5player(?:-new)?|(?:/[a-z]{2}_[A-Z]{2})?/base)?\.(?P<ext>[a-z]+)$',
			playerUrl)
		if not id_m:
			raise extractorError('Cannot identify player %r' % playerUrl)

		player_type = id_m.group('ext')
		if player_type != 'js':
			raise extractorError('Invalid player type %r' % player_type)

		# use algoCache
		slen = len(s)
		player_id = (playerUrl, self._signature_cache_id(s))
		if player_id not in self._player_cache:
			# get player HTML 5 script
			try:
				opener = requests.session()
				response = opener.get(playerUrl)
				self.playerData = response.content
				encoding = 'utf-8'
				try:
					self.playerData = self.playerData.decode(encoding, 'replace')
				except LookupError:
					self.playerData = self.playerData.decode('utf-8', 'replace')
			except Exception as e:
				print('[CVevoSignAlgoExtractor] Unable to download playerUrl webpage')
				print exception_err(e)
				self._cleanTmpVariables()
				return ''

			try:
				func = self._parse_sig_js()
				test_string = u''.join(map(compat_chr, range(slen)))
				cache_res = func(test_string)
				cache_spec = [ord(c) for c in cache_res]
				self._player_cache[player_id] = func
			except Exception as e:
				print exception_err(e)
				self._cleanTmpVariables()
				return ''

		func = self._player_cache[player_id]
		s_out = func(s)

		# free not needed data
		self._cleanTmpVariables()

		return s_out

	def _parse_sig_js(self):
		funcname = self._search_regex(
			(r'(["\'])signature\1\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
			r'\.sig\|\|(?P<sig>[a-zA-Z0-9$]+)\(',
			r'yt\.akamaized\.net/\)\s*\|\|\s*.*?\s*c\s*&&\s*d\.set\([^,]+\s*,\s*(?:encodeURIComponent\s*\()?(?P<sig>[a-zA-Z0-9$]+)\(',
			r'\bc\s*&&\s*d\.set\([^,]+\s*,\s*(?:encodeURIComponent\s*\()?\s*(?P<sig>[a-zA-Z0-9$]+)\(',
			r'\bc\s*&&\s*d\.set\([^,]+\s*,\s*\([^)]*\)\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\('),
			self.playerData, 'Initial JS player signature function name', group='sig')

		jsi = JSInterpreter(self.playerData)
		initial_function = jsi.extract_function(funcname)
		return lambda s: initial_function([s])

	def _search_regex(self, pattern, string, name, default=_NO_DEFAULT, fatal=True, flags=0, group=None):
		"""
		Perform a regex search on the given string, using a single or a list of
		patterns returning the first matching group.
		In case of failure return a default value or raise a WARNING or a
		RegexNotFoundError, depending on fatal, specifying the field name.
		"""
		if isinstance(pattern, (str, compat_str, compiled_regex_type)):
			mobj = re.search(pattern, string, flags)
		else:
			for p in pattern:
				mobj = re.search(p, string, flags)
				if mobj:
					break
		if mobj:
			if group is None:
				# return the first matching group
				return next(g for g in mobj.groups() if g is not None)
			else:
				return mobj.group(group)
		elif default is not _NO_DEFAULT:
			return default
		else:
			print '[CVevoSignAlgoExtractor] Unable to extract'
			return None

	def _signature_cache_id(self, example_sig):
		""" Return a string representation of a signature """
		return u'.'.join(compat_str(len(part)) for part in example_sig.split('.'))

decryptor = CVevoSignAlgoExtractor()