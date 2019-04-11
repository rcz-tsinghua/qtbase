#!/usr/bin/env python3
#############################################################################
##
## Copyright (C) 2018 The Qt Company Ltd.
## Contact: https://www.qt.io/licensing/
##
## This file is part of the plugins of the Qt Toolkit.
##
## $QT_BEGIN_LICENSE:GPL-EXCEPT$
## Commercial License Usage
## Licensees holding valid commercial Qt licenses may use this file in
## accordance with the commercial license agreement provided with the
## Software or, alternatively, in accordance with the terms contained in
## a written agreement between you and The Qt Company. For licensing terms
## and conditions see https://www.qt.io/terms-conditions. For further
## information use the contact form at https://www.qt.io/contact-us.
##
## GNU General Public License Usage
## Alternatively, this file may be used under the terms of the GNU
## General Public License version 3 as published by the Free Software
## Foundation with exceptions as appearing in the file LICENSE.GPL3-EXCEPT
## included in the packaging of this file. Please review the following
## information to ensure the GNU General Public License requirements will
## be met: https://www.gnu.org/licenses/gpl-3.0.html.
##
## $QT_END_LICENSE$
##
#############################################################################


from __future__ import annotations

from argparse import ArgumentParser
import copy
import xml.etree.ElementTree as ET
from itertools import chain
import os.path
import re
import io
import typing

from sympy.logic import (simplify_logic, And, Or, Not,)
import pyparsing as pp

from helper import map_qt_library, map_qt_base_library, featureName, \
    substitute_platform, substitute_libs


def _parse_commandline():
    parser = ArgumentParser(description='Generate CMakeLists.txt files from .'
                            'pro files.')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='Turn on all debug output')
    parser.add_argument('--debug-parser', dest='debug_parser',
                        action='store_true',
                        help='Print debug output from qmake parser.')
    parser.add_argument('--debug-parse-result', dest='debug_parse_result',
                        action='store_true',
                        help='Dump the qmake parser result.')
    parser.add_argument('--debug-parse-dictionary',
                        dest='debug_parse_dictionary', action='store_true',
                        help='Dump the qmake parser result as dictionary.')
    parser.add_argument('--debug-pro-structure', dest='debug_pro_structure',
                        action='store_true',
                        help='Dump the structure of the qmake .pro-file.')
    parser.add_argument('--debug-full-pro-structure',
                        dest='debug_full_pro_structure', action='store_true',
                        help='Dump the full structure of the qmake .pro-file '
                        '(with includes).')
    parser.add_argument('files', metavar='<.pro/.pri file>', type=str,
                        nargs='+', help='The .pro/.pri file to process')

    return parser.parse_args()


def process_qrc_file(target: str, filepath: str, base_dir: str = '') -> str:
    assert(target)
    resource_name = os.path.splitext(os.path.basename(filepath))[0]
    base_dir = os.path.join('' if base_dir == '.' else base_dir, os.path.dirname(filepath))

    tree = ET.parse(filepath)
    root = tree.getroot()
    assert(root.tag == 'RCC')

    output = ''

    resource_count = 0
    for resource in root:
        assert(resource.tag == 'qresource')
        lang = resource.get('lang', '')
        prefix = resource.get('prefix', '')

        full_resource_name = resource_name + (str(resource_count) if resource_count > 0 else '')

        files: typing.Dict[str, str] = {}
        for file in resource:
            path = file.text
            assert path

            # Get alias:
            alias = file.get('alias', '')
            files[path] = alias

        sorted_files = sorted(files.keys())

        assert(sorted_files)

        for source in sorted_files:
            alias = files[source]
            if alias:
                full_source = os.path.join(base_dir, source)
                output += 'set_source_files_properties("{}"\n' \
                          '    PROPERTIES alias "{}")\n'.format(full_source, alias)

        params = ''
        if lang:
            params += ' LANG "{}"'.format(lang)
        if prefix:
            params += ' PREFIX "{}"'.format(prefix)
        if base_dir:
            params += ' BASE "{}"'.format(base_dir)
        output += 'add_qt_resource({} "{}"{} FILES\n    {})\n'.format(target, full_resource_name,
                                                                      params,
                                                                      '\n    '.join(sorted_files))

        resource_count += 1

    return output


def fixup_linecontinuation(contents: str) -> str:
    contents = re.sub(r'([^\t ])\\[ \t]*\n', '\\1 \\\n', contents)
    contents = re.sub(r'\\[ \t]*\n', '\\\n', contents)

    return contents


def spaces(indent: int) -> str:
    return '    ' * indent


def map_to_file(f: str, scope: Scope, *, is_include: bool = False) -> str:
    assert('$$' not in f)

    if f.startswith('${'): # Some cmake variable is prepended
        return f

    base_dir = scope.currentdir if is_include else scope.basedir
    f = os.path.join(base_dir, f)

    while f.startswith('./'):
        f = f[2:]
    return f


def handle_vpath(source: str, base_dir: str, vpath: typing.List[str]) -> str:
    assert('$$' not in source)

    if not source:
        return ''

    if not vpath:
        return source

    if os.path.exists(os.path.join(base_dir, source)):
        return source

    variable_pattern = re.compile(r'\$\{[A-Za-z0-9_]+\}')
    match = re.match(variable_pattern, source)
    if match:
        # a complex, variable based path, skipping validation
        # or resolving
        return source

    for v in vpath:
        fullpath = os.path.join(v, source)
        if os.path.exists(fullpath):
            relpath = os.path.relpath(fullpath, base_dir)
            return relpath

    print('    XXXX: Source {}: Not found.'.format(source))
    return '{}-NOTFOUND'.format(source)


class Operation:
    def __init__(self, value):
        if isinstance(value, list):
            self._value = value
        else:
            self._value = [str(value), ]

    def process(self, key, input, transformer):
        assert(False)

    def __repr__(self):
        assert(False)

    def _dump(self):
        if not self._value:
            return '<NOTHING>'

        if not isinstance(self._value, list):
            return '<NOT A LIST>'

        result = []
        for i in self._value:
            if not i:
                result.append('<NONE>')
            else:
                result.append(str(i))
        return '"' + '", "'.join(result) + '"'


class AddOperation(Operation):
    def process(self, key, input, transformer):
        return input + transformer(self._value)

    def __repr__(self):
        return '+({})'.format(self._dump())


class UniqueAddOperation(Operation):
    def process(self, key, input, transformer):
        result = input
        for v in transformer(self._value):
            if v not in result:
                result.append(v)
        return result

    def __repr__(self):
        return '*({})'.format(self._dump())


class SetOperation(Operation):
    def process(self, key, input, transformer):
        values = []  # typing.List[str]
        for v in self._value:
            if v != '$$' + key:
                values.append(v)
            else:
                values += input

        if transformer:
            return list(transformer(values))
        else:
            return values

    def __repr__(self):
        return '=({})'.format(self._dump())


class RemoveOperation(Operation):
    def __init__(self, value):
        super().__init__(value)

    def process(self, key, input, transformer):
        input_set = set(input)
        value_set = set(self._value)
        result = []

        # Add everything that is not going to get removed:
        for v in input:
            if v not in value_set:
                result += [v,]

        # Add everything else with removal marker:
        for v in transformer(self._value):
            if v not in input_set:
                result += ['-{}'.format(v), ]

        return result

    def __repr__(self):
        return '-({})'.format(self._dump())


class Scope(object):

    SCOPE_ID: int = 1

    def __init__(self, *,
                 parent_scope: typing.Optional[Scope],
                 file: typing.Optional[str] = None, condition: str = '',
                 base_dir: str = '',
                 operations: typing.Mapping[str, typing.List[Operation]] = {
                    'QT_SOURCE_TREE': [SetOperation('${PROJECT_SOURCE_DIR}')],
                    'QT_BUILD_TREE': [SetOperation('${PROJECT_BUILD_DIR}')],
                 }) -> None:
        if parent_scope:
            parent_scope._add_child(self)
        else:
            self._parent = None  # type: typing.Optional[Scope]

        self._basedir = base_dir
        if file:
            self._currentdir = os.path.dirname(file)
        if not self._currentdir:
            self._currentdir = '.'
        if not self._basedir:
            self._basedir = self._currentdir

        self._scope_id = Scope.SCOPE_ID
        Scope.SCOPE_ID += 1
        self._file = file
        self._condition = map_condition(condition)
        self._children = []  # type: typing.List[Scope]
        self._included_children = []  # type: typing.List[Scope]
        self._operations = copy.deepcopy(operations)
        self._visited_keys = set()  # type: typing.Set[str]
        self._total_condition = None  # type: typing.Optional[str]

    def __repr__(self):
        return '{}:{}:{}:{}:{}'.format(self._scope_id,
                                       self._basedir, self._currentdir,
                                       self._file, self._condition or '<TRUE>')

    def reset_visited_keys(self):
        self._visited_keys = set()

    def merge(self, other: 'Scope') -> None:
        assert self != other
        self._included_children.append(other)

    @property
    def scope_debug(self) -> bool:
        merge = self.get_string('PRO2CMAKE_SCOPE_DEBUG').lower()
        return merge and (merge == '1' or merge == 'on' or merge == 'yes' or merge == 'true')

    @property
    def parent(self) -> typing.Optional[Scope]:
        return self._parent

    @property
    def basedir(self) -> str:
        return self._basedir

    @property
    def currentdir(self) -> str:
        return self._currentdir

    def can_merge_condition(self):
        if self._condition == 'else':
            return False
        if self._operations:
            return False

        child_count = len(self._children)
        if child_count == 0 or child_count > 2:
            return False
        assert child_count != 1 or self._children[0]._condition != 'else'
        return child_count == 1 or self._children[1]._condition == 'else'

    def settle_condition(self):
        new_children: typing.List[Scope] = []
        for c in self._children:
            c.settle_condition()

            if c.can_merge_condition():
                child = c._children[0]
                child._condition = '({}) AND ({})'.format(c._condition, child._condition)
                new_children += c._children
            else:
                new_children.append(c)
        self._children = new_children

    @staticmethod
    def FromDict(parent_scope: typing.Optional['Scope'],
                 file: str, statements, cond: str = '', base_dir: str = '') -> Scope:
        scope = Scope(parent_scope=parent_scope, file=file, condition=cond, base_dir=base_dir)
        for statement in statements:
            if isinstance(statement, list):  # Handle skipped parts...
                assert not statement
                continue

            operation = statement.get('operation', None)
            if operation:
                key = statement.get('key', '')
                value = statement.get('value', [])
                assert key != ''

                if operation == '=':
                    scope._append_operation(key, SetOperation(value))
                elif operation == '-=':
                    scope._append_operation(key, RemoveOperation(value))
                elif operation == '+=':
                    scope._append_operation(key, AddOperation(value))
                elif operation == '*=':
                    scope._append_operation(key, UniqueAddOperation(value))
                else:
                    print('Unexpected operation "{}" in scope "{}".'
                          .format(operation, scope))
                    assert(False)

                continue

            condition = statement.get('condition', None)
            if condition:
                Scope.FromDict(scope, file,
                               statement.get('statements'), condition,
                               scope.basedir)

                else_statements = statement.get('else_statements')
                if else_statements:
                    Scope.FromDict(scope, file, else_statements,
                                   'else', scope.basedir)
                continue

            loaded = statement.get('loaded')
            if loaded:
                scope._append_operation('_LOADED', UniqueAddOperation(loaded))
                continue

            option = statement.get('option', None)
            if option:
                scope._append_operation('_OPTION', UniqueAddOperation(option))
                continue

            included = statement.get('included', None)
            if included:
                scope._append_operation('_INCLUDED',
                                        UniqueAddOperation(included))
                continue

        scope.settle_condition()

        if scope.scope_debug:
            print('..... [SCOPE_DEBUG]: Created scope {}:'.format(scope))
            scope.dump(indent=1)
            print('..... [SCOPE_DEBUG]: <<END OF SCOPE>>')
        return scope

    def _append_operation(self, key: str, op: Operation) -> None:
        if key in self._operations:
            self._operations[key].append(op)
        else:
            self._operations[key] = [op, ]

    @property
    def file(self) -> str:
        return self._file or ''

    @property
    def cMakeListsFile(self) -> str:
        assert self.basedir
        return os.path.join(self.basedir, 'CMakeLists.txt')

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def total_condition(self) -> typing.Optional[str]:
        return self._total_condition

    @total_condition.setter
    def total_condition(self, condition: str) -> None:
        self._total_condition = condition

    def _add_child(self, scope: 'Scope') -> None:
        scope._parent = self
        self._children.append(scope)

    @property
    def children(self) -> typing.List['Scope']:
        result = list(self._children)
        for include_scope in self._included_children:
            result += include_scope._children
        return result

    def dump(self, *, indent: int = 0) -> None:
        ind = '    ' * indent
        print('{}Scope "{}":'.format(ind, self))
        if self.total_condition:
            print('{}  Total condition = {}'.format(ind, self.total_condition))
        print('{}  Keys:'.format(ind))
        keys = self._operations.keys()
        if not keys:
            print('{}    -- NONE --'.format(ind))
        else:
            for k in sorted(keys):
                print('{}    {} = "{}"'
                      .format(ind, k, self._operations.get(k, [])))
        print('{}  Children:'.format(ind))
        if not self._children:
            print('{}    -- NONE --'.format(ind))
        else:
            for c in self._children:
                c.dump(indent=indent + 1)
        print('{}  Includes:'.format(ind))
        if not self._included_children:
            print('{}    -- NONE --'.format(ind))
        else:
            for c in self._included_children:
                c.dump(indent=indent + 1)

    def dump_structure(self, *, type: str = 'ROOT', indent: int = 0) -> None:
        print('{}{}: {}'.format(spaces(indent), type, self))
        for i in self._included_children:
            i.dump_structure(type='INCL', indent=indent + 1)
        for i in self._children:
            i.dump_structure(type='CHLD', indent=indent + 1)

    @property
    def keys(self):
        return self._operations.keys()

    @property
    def visited_keys(self):
        return self._visited_keys

    def _evalOps(self, key: str,
                 transformer: typing.Optional[typing.Callable[[Scope, typing.List[str]], typing.List[str]]],
                 result: typing.List[str], *, inherrit: bool = False) \
            -> typing.List[str]:
        self._visited_keys.add(key)

        # Inherrit values from above:
        if self._parent and inherrit:
            result = self._parent._evalOps(key, transformer, result)

        if transformer:
            op_transformer = lambda files: transformer(self, files)
        else:
            op_transformer = lambda files: files

        for op in self._operations.get(key, []):
            result = op.process(key, result, op_transformer)

        for ic in self._included_children:
            result = list(ic._evalOps(key, transformer, result))

        return result

    def get(self, key: str, *, ignore_includes: bool = False, inherrit: bool = False) -> typing.List[str]:
        if key == 'PWD':
            return ['${CMAKE_CURRENT_SOURCE_DIR}/' + os.path.relpath(self.currentdir, self.basedir),]
        if key == 'OUT_PWD':
            return ['${CMAKE_CURRENT_BUILD_DIR}/' + os.path.relpath(self.currentdir, self.basedir),]

        return self._evalOps(key, None, [], inherrit=inherrit)

    def get_string(self, key: str, default: str = '') -> str:
        v = self.get(key)
        if len(v) == 0:
            return default
        assert len(v) == 1
        return v[0]

    def _map_files(self, files: typing.List[str], *,
                   use_vpath: bool = True, is_include: bool = False) -> typing.List[str]:

        expanded_files = []  # typing.List[str]
        for f in files:
            r = self._expand_value(f)
            expanded_files += r

        mapped_files = list(map(lambda f: map_to_file(f, self, is_include=is_include), expanded_files))

        if use_vpath:
            result = list(map(lambda f: handle_vpath(f, self.basedir, self.get('VPATH', inherrit=True)), mapped_files))
        else:
            result = mapped_files

        # strip ${CMAKE_CURRENT_SOURCE_DIR}:
        result = list(map(lambda f: f[28:] if f.startswith('${CMAKE_CURRENT_SOURCE_DIR}/') else f, result))

        return result

    def get_files(self, key: str, *, use_vpath: bool = False,
                  is_include: bool = False) -> typing.List[str]:
        transformer = lambda scope, files: scope._map_files(files, use_vpath=use_vpath, is_include=is_include)
        return list(self._evalOps(key, transformer, []))

    def _expand_value(self, value: str) -> typing.List[str]:
        result = value
        pattern = re.compile(r'\$\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?')
        match = re.search(pattern, result)
        while match:
            old_result = result
            if match.group(0) == value:
                return self.get(match.group(1))

            replacement = self.get(match.group(1))
            replacement_str = replacement[0] if replacement else ''
            result = result[:match.start()] \
                     + replacement_str \
                     + result[match.end():]

            if result == old_result:
                return [result,] # Do not go into infinite loop

            match = re.search(pattern, result)
        return [result,]

    def expand(self, key: str) -> typing.List[str]:
        value = self.get(key)
        result: typing.List[str] = []
        assert isinstance(value, list)
        for v in value:
            result += self._expand_value(v)
        return result

    def expandString(self, key: str) -> str:
        result = self._expand_value(self.get_string(key))
        assert len(result) == 1
        return result[0]

    @property
    def TEMPLATE(self) -> str:
        return self.get_string('TEMPLATE', 'app')

    def _rawTemplate(self) -> str:
        return self.get_string('TEMPLATE')

    @property
    def TARGET(self) -> str:
        return self.get_string('TARGET') \
            or os.path.splitext(os.path.basename(self.file))[0]

    @property
    def _INCLUDED(self) -> typing.List[str]:
        return self.get('_INCLUDED')


class QmakeParser:
    def __init__(self, *, debug: bool = False) -> None:
        self._Grammar = self._generate_grammar(debug)

    def _generate_grammar(self, debug: bool):
        # Define grammar:
        pp.ParserElement.setDefaultWhitespaceChars(' \t')

        LC = pp.Suppress(pp.Literal('\\\n'))
        EOL = pp.Suppress(pp.LineEnd())
        Else = pp.Keyword('else')
        Identifier = pp.Word(pp.alphas + '_', bodyChars=pp.alphanums+'_-./')
        BracedValue = pp.nestedExpr(ignoreExpr=pp.quotedString \
                                        | pp.QuotedString(quoteChar='$(',
                                                          endQuoteChar=')',
                                                          escQuote='\\',
                                                          unquoteResults=False)
                                   ).setParseAction(lambda s, l, t: ['(', *t[0], ')'])

        Substitution \
            = pp.Combine(pp.Literal('$')
                         + (((pp.Literal('$') + Identifier
                              + pp.Optional(pp.nestedExpr()))
                             | (pp.Literal('(') + Identifier + pp.Literal(')'))
                             | (pp.Literal('{') + Identifier + pp.Literal('}'))
                             | (pp.Literal('$') + pp.Literal('{')
                                + Identifier + pp.Optional(pp.nestedExpr())
                                + pp.Literal('}'))
                             | (pp.Literal('$') + pp.Literal('[') + Identifier
                                + pp.Literal(']'))
                             )))
        LiteralValuePart = pp.Word(pp.printables, excludeChars='$#{}()')
        SubstitutionValue \
            = pp.Combine(pp.OneOrMore(Substitution | LiteralValuePart
                                      | pp.Literal('$')))
        Value = pp.NotAny(Else | pp.Literal('}') | EOL) \
            + (pp.QuotedString(quoteChar='"', escChar='\\')
                | SubstitutionValue
                | BracedValue)

        Values = pp.ZeroOrMore(Value + pp.Optional(LC))('value')

        Op = pp.Literal('=') | pp.Literal('-=') | pp.Literal('+=') \
            | pp.Literal('*=')

        Key = Identifier

        Operation = Key('key') + pp.Optional(LC) \
            + Op('operation') + pp.Optional(LC) \
            + Values('value')
        CallArgs = pp.Optional(LC) + pp.nestedExpr()\

        def parse_call_args(results):
            out = ''
            for item in chain(*results):
                if isinstance(item, str):
                    out += item
                else:
                    out += "(" + parse_call_args(item) + ")"
            return out

        CallArgs.setParseAction(parse_call_args)
        Load = pp.Keyword('load') + CallArgs('loaded')
        Include = pp.Keyword('include') + CallArgs('included')
        Option = pp.Keyword('option') + CallArgs('option')
        DefineTestDefinition = pp.Suppress(pp.Keyword('defineTest') + CallArgs
             + pp.nestedExpr(opener='{', closer='}', ignoreExpr=pp.LineEnd()))  # ignore the whole thing...
        ForLoop = pp.Suppress(pp.Keyword('for') + CallArgs
             + pp.nestedExpr(opener='{', closer='}', ignoreExpr=pp.LineEnd()))  # ignore the whole thing...
        ForLoopSingleLine = pp.Suppress(pp.Keyword('for') + CallArgs
             + pp.Literal(':') + pp.SkipTo(EOL, ignore=LC))  # ignore the whole thing...
        FunctionCall = pp.Suppress(Identifier + pp.nestedExpr())

        Scope = pp.Forward()

        Statement = pp.Group(Load | Include | Option | ForLoop | ForLoopSingleLine \
            | DefineTestDefinition | FunctionCall | Operation)
        StatementLine = Statement + (EOL | pp.FollowedBy('}'))
        StatementGroup = pp.ZeroOrMore(StatementLine | Scope | pp.Suppress(EOL))

        Block = pp.Suppress('{')  + pp.Optional(LC | EOL) \
            + StatementGroup + pp.Optional(LC | EOL) \
            + pp.Suppress('}') + pp.Optional(LC | EOL)

        ConditionEnd = pp.FollowedBy((pp.Optional(pp.White())
            + pp.Optional(LC) + (pp.Literal(':') \
                 | pp.Literal('{') \
                 | pp.Literal('|'))))
        ConditionPart = ((pp.Optional('!') + Identifier + pp.Optional(BracedValue)) \
            ^ pp.CharsNotIn('#{}|:=\\\n')) + pp.Optional(LC) + ConditionEnd
        Condition = pp.Combine(ConditionPart \
            + pp.ZeroOrMore((pp.Literal('|') ^ pp.Literal(':')) \
            + ConditionPart))
        Condition.setParseAction(lambda x: ' '.join(x).strip().replace(':', ' && ').strip(' && '))

        SingleLineScope = pp.Suppress(pp.Literal(':')) + pp.Optional(LC) \
            + pp.Group(Block | (Statement + EOL))('statements')
        MultiLineScope = pp.Optional(LC) + Block('statements')

        SingleLineElse = pp.Suppress(pp.Literal(':')) + pp.Optional(LC) \
            + (Scope | Block | (Statement + pp.Optional(EOL)))
        MultiLineElse = Block
        ElseBranch = pp.Suppress(Else) + (SingleLineElse | MultiLineElse)
        Scope <<= pp.Optional(LC) \
            + pp.Group(Condition('condition') \
            + (SingleLineScope | MultiLineScope) \
            + pp.Optional(ElseBranch)('else_statements'))

        if debug:
            for ename in 'LC EOL ' \
                         'Condition ConditionPart ConditionEnd ' \
                         'Else ElseBranch SingleLineElse MultiLineElse ' \
                         'SingleLineScope MultiLineScope ' \
                         'Identifier ' \
                         'Key Op Values Value BracedValue ' \
                         'Scope Block ' \
                         'StatementGroup StatementLine Statement '\
                         'Load Include Option DefineTestDefinition ForLoop ' \
                         'FunctionCall CallArgs Operation'.split():
                expr = locals()[ename]
                expr.setName(ename)
                expr.setDebug()

        Grammar = StatementGroup('statements')
        Grammar.ignore(pp.pythonStyleComment())

        return Grammar

    def parseFile(self, file: str):
        print('Parsing \"{}\"...'.format(file))
        try:
            with open(file, 'r') as file_fd:
                contents = file_fd.read()

            old_contents = contents
            contents = fixup_linecontinuation(contents)

            if old_contents != contents:
                print('Warning: Fixed line continuation in .pro-file!\n'
                      '         Position information in Parsing output might be wrong!')
            result = self._Grammar.parseString(contents, parseAll=True)
        except pp.ParseException as pe:
            print(pe.line)
            print(' '*(pe.col-1) + '^')
            print(pe)
            raise pe
        return result


def parseProFile(file: str, *, debug=False):
    parser = QmakeParser(debug=debug)
    return parser.parseFile(file)


def map_condition(condition: str) -> str:
    condition = re.sub(r'\bif\s*\((.*?)\)', r'\1', condition)
    condition = re.sub(r'\bisEmpty\s*\((.*?)\)', r'\1_ISEMPTY', condition)
    condition = re.sub(r'\bcontains\s*\((.*?),\s*"?(.*?)"?\)',
                       r'\1___contains___\2', condition)
    condition = re.sub(r'\bequals\s*\((.*?),\s*"?(.*?)"?\)',
                       r'\1___equals___\2', condition)
    condition = re.sub(r'\s*==\s*', '___STREQUAL___', condition)

    condition = condition.replace('*', '_x_')
    condition = condition.replace('.$$', '__ss_')
    condition = condition.replace('$$', '_ss_')

    condition = condition.replace('!', 'NOT ')
    condition = condition.replace('&&', ' AND ')
    condition = condition.replace('|', ' OR ')

    cmake_condition = ''
    for part in condition.split():
        # some features contain e.g. linux, that should not be
        # turned upper case
        feature = re.match(r"(qtConfig|qtHaveModule)\(([a-zA-Z0-9_-]+)\)",
                           part)
        if feature:
            if (feature.group(1) == "qtHaveModule"):
                part = 'TARGET {}'.format(map_qt_library(feature.group(2)))
            else:
                feature = featureName(feature.group(2))
                if feature.startswith('system_') and substitute_libs(feature[7:]) != feature[7:]:
                    # Qt6 always uses system libraries!
                    part = 'ON'
                elif feature == 'dlopen':
                    part = 'ON'
                else:
                    part = 'QT_FEATURE_' + feature
        else:
            part = substitute_platform(part)

        part = part.replace('true', 'ON')
        part = part.replace('false', 'OFF')
        cmake_condition += ' ' + part
    return cmake_condition.strip()


def handle_subdir(scope: Scope, cm_fh: typing.IO[str], *,
                  indent: int = 0) -> None:
    ind = '    ' * indent
    for sd in scope.get_files('SUBDIRS'):
        if os.path.isdir(sd):
            cm_fh.write('{}add_subdirectory({})\n'.format(ind, sd))
        elif os.path.isfile(sd):
            subdir_result = parseProFile(sd, debug=False)
            subdir_scope \
                = Scope.FromDict(scope, sd,
                                 subdir_result.asDict().get('statements'),
                                 '', scope.basedir)

            do_include(subdir_scope)
            cmakeify_scope(subdir_scope, cm_fh, indent=indent)
        elif sd.startswith('-'):
            cm_fh.write('{}### remove_subdirectory'
                        '("{}")\n'.format(ind, sd[1:]))
        else:
            print('    XXXX: SUBDIR {} in {}: Not found.'.format(sd, scope))

    for c in scope.children:
        cond = c.condition
        if cond == 'else':
            cm_fh.write('\n{}else()\n'.format(ind))
        elif cond:
            cm_fh.write('\n{}if({})\n'.format(ind, cond))

        handle_subdir(c, cm_fh, indent=indent + 1)

        if cond:
            cm_fh.write('{}endif()\n'.format(ind))


def sort_sources(sources: typing.List[str]) -> typing.List[str]:
    to_sort = {}  # type: typing.Dict[str, typing.List[str]]
    for s in sources:
        if s is None:
            continue

        dir = os.path.dirname(s)
        base = os.path.splitext(os.path.basename(s))[0]
        if base.endswith('_p'):
            base = base[:-2]
        sort_name = os.path.join(dir, base)

        array = to_sort.get(sort_name, [])
        array.append(s)

        to_sort[sort_name] = array

    lines = []
    for k in sorted(to_sort.keys()):
        lines.append(' '.join(sorted(to_sort[k])))

    return lines


def write_header(cm_fh: typing.IO[str], name: str,
                 typename: str, *, indent: int = 0):
    cm_fh.write('{}###########################################'
                '##########################\n'.format(spaces(indent)))
    cm_fh.write('{}## {} {}:\n'.format(spaces(indent), name, typename))
    cm_fh.write('{}###########################################'
                '##########################\n\n'.format(spaces(indent)))


def write_scope_header(cm_fh: typing.IO[str], *, indent: int = 0):
    cm_fh.write('\n{}## Scopes:\n'.format(spaces(indent)))
    cm_fh.write('{}###########################################'
                '##########################\n'.format(spaces(indent)))


def write_source_file_list(cm_fh: typing.IO[str], scope, cmake_parameter: str,
                           keys: typing.List[str], indent: int = 0, *,
                           header: str = '', footer: str = ''):
    ind = spaces(indent)

    # collect sources
    sources: typing.List[str] = []
    for key in keys:
        sources += scope.get_files(key, use_vpath=True)

    if not sources:
        return

    cm_fh.write(header)
    extra_indent = ''
    if cmake_parameter:
        cm_fh.write('{}    {}\n'.format(ind, cmake_parameter))
        extra_indent = '    '
    for s in sort_sources(sources):
        cm_fh.write('{}    {}{}\n'.format(ind, extra_indent, s))
    cm_fh.write(footer)


def write_library_list(cm_fh: typing.IO[str], cmake_keyword: str,
                       dependencies: typing.List[str], *, indent: int = 0):
    dependencies_to_print = []
    is_framework = False

    for d in dependencies:
        if d == '-framework':
            is_framework = True
            continue
        if is_framework:
            d = '${FW%s}' % d
        if d.startswith('-l'):
            d = d[2:]

        if d.startswith('-'):
            d = '# Remove: {}'.format(d[1:])
        else:
            d = substitute_libs(d)
        dependencies_to_print.append(d)
        is_framework = False

    if dependencies_to_print:
        ind = spaces(indent)
        cm_fh.write('{}    {}\n'.format(ind, cmake_keyword))
        for d in sorted(list(set(dependencies_to_print))):
            cm_fh.write('{}        {}\n'.format(ind, d))



def write_library_section(cm_fh: typing.IO[str], scope: Scope,
                          public: typing.List[str],
                          private: typing.List[str],
                          mixed: typing.List[str], *,
                          indent: int = 0, known_libraries=set()):
    public_dependencies = []  # typing.List[str]
    private_dependencies = []  # typing.List[str]

    for key in public:
        public_dependencies += [map_qt_library(q) for q in scope.expand(key)
                                if map_qt_library(q) not in known_libraries]
    for key in private:
        private_dependencies += [map_qt_library(q) for q in scope.expand(key)
                                 if map_qt_library(q) not in known_libraries]
    for key in mixed:
        for lib in scope.expand(key):
            mapped_lib = map_qt_library(lib)
            if mapped_lib in known_libraries:
                continue

            if mapped_lib.endswith('Private'):
                private_dependencies.append(mapped_lib)
                public_dependencies.append(mapped_lib[:-7])
            else:
                public_dependencies.append(mapped_lib)

    write_library_list(cm_fh, 'LIBRARIES', private_dependencies, indent=indent)
    write_library_list(cm_fh, 'PUBLIC_LIBRARIES', public_dependencies, indent=indent)



def write_sources_section(cm_fh: typing.IO[str], scope: Scope, *,
                          indent: int = 0, known_libraries=set()):
    ind = spaces(indent)

    # mark RESOURCES as visited:
    scope.get('RESOURCES')

    plugin_type = scope.get_string('PLUGIN_TYPE')

    if plugin_type:
        cm_fh.write('{}    TYPE {}\n'.format(ind, plugin_type))

    source_keys: typing.List[str] = []
    write_source_file_list(cm_fh, scope, 'SOURCES',
                           ['SOURCES', 'HEADERS', 'OBJECTIVE_SOURCES', 'NO_PCH_SOURCES', 'FORMS'],
                           indent)

    write_source_file_list(cm_fh, scope, 'DBUS_ADAPTOR_SOURCES', ['DBUS_ADAPTORS',], indent)
    dbus_adaptor_flags = scope.expand('QDBUSXML2CPP_ADAPTOR_HEADER_FLAGS')
    if dbus_adaptor_flags:
        cm_fh.write('{}    DBUS_ADAPTOR_FLAGS\n'.format(ind))
        cm_fh.write('{}        "{}"\n'.format(ind, '" "'.join(dbus_adaptor_flags)))

    write_source_file_list(cm_fh, scope, 'DBUS_INTERFACE_SOURCES', ['DBUS_INTERFACES',], indent)
    dbus_interface_flags = scope.expand('QDBUSXML2CPP_INTERFACE_HEADER_FLAGS')
    if dbus_interface_flags:
        cm_fh.write('{}    DBUS_INTERFACE_FLAGS\n'.format(ind))
        cm_fh.write('{}        "{}"\n'.format(ind, '" "'.join(dbus_interface_flags)))

    defines = scope.expand('DEFINES')
    defines += [d[2:] for d in scope.expand('QMAKE_CXXFLAGS') if d.startswith('-D')]
    if defines:
        cm_fh.write('{}    DEFINES\n'.format(ind))
        for d in defines:
            d = d.replace('=\\\\\\"$$PWD/\\\\\\"',
                          '="${CMAKE_CURRENT_SOURCE_DIR}/"')
            cm_fh.write('{}        {}\n'.format(ind, d))
    includes = scope.get_files('INCLUDEPATH')
    if includes:
        cm_fh.write('{}    INCLUDE_DIRECTORIES\n'.format(ind))
        for i in includes:
            i = i.rstrip('/') or ('/')
            cm_fh.write('{}        {}\n'.format(ind, i))

    write_library_section(cm_fh, scope,
                          ['QMAKE_USE', 'LIBS'],
                          ['QT_FOR_PRIVATE', 'QMAKE_USE_PRIVATE', 'QMAKE_USE_FOR_PRIVATE', 'LIBS_PRIVATE'],
                          ['QT',],
                          indent=indent, known_libraries=known_libraries)

    compile_options = [d for d in scope.expand('QMAKE_CXXFLAGS') if not d.startswith('-D')]
    if compile_options:
        cm_fh.write('{}    COMPILE_OPTIONS\n'.format(ind))
        for co in compile_options:
            cm_fh.write('{}        "{}"\n'.format(ind, co))

    link_options = scope.get('QMAKE_LFLAGS')
    if link_options:
        cm_fh.write('{}    LINK_OPTIONS\n'.format(ind))
        for lo in link_options:
            cm_fh.write('{}        "{}"\n'.format(ind, lo))

    moc_options = scope.get('QMAKE_MOC_OPTIONS')
    if moc_options:
        cm_fh.write('{}    MOC_OPTIONS\n'.format(ind))
        for mo in moc_options:
            cm_fh.write('{}        "{}"\n'.format(ind, mo))


def is_simple_condition(condition: str) -> bool:
    return ' ' not in condition \
        or (condition.startswith('NOT ') and ' ' not in condition[4:])


def write_ignored_keys(scope: Scope, indent: str) -> str:
    result = ''
    ignored_keys = scope.keys - scope.visited_keys
    for k in sorted(ignored_keys):
        if k == '_INCLUDED' or k == 'TARGET' or k == 'QMAKE_DOCS' or k == 'QT_SOURCE_TREE' \
                or k == 'QT_BUILD_TREE' or k == 'TRACEPOINT_PROVIDER':
            # All these keys are actually reported already
            continue
        values = scope.get(k)
        value_string = '<EMPTY>' if not values \
            else '"' + '" "'.join(scope.get(k)) + '"'
        result += '{}# {} = {}\n'.format(indent, k, value_string)

    if result:
        result = '\n#### Keys ignored in scope {}:\n{}'.format(scope, result)

    return result


def _iterate_expr_tree(expr, op, matches):
    assert expr.func == op
    keepers = ()
    for arg in expr.args:
        if arg in matches:
            matches = tuple(x for x in matches if x != arg)
        elif arg == op:
            (matches, extra_keepers) = _iterate_expr_tree(arg, op, matches)
            keepers = (*keepers, *extra_keepers)
        else:
            keepers = (*keepers, arg)
    return matches, keepers


def _simplify_expressions(expr, op, matches, replacement):
    for arg in expr.args:
        expr = expr.subs(arg, _simplify_expressions(arg, op, matches,
                                                    replacement))

    if expr.func == op:
        (to_match, keepers) = tuple(_iterate_expr_tree(expr, op, matches))
        if len(to_match) == 0:
            # build expression with keepers and replacement:
            if keepers:
                start = replacement
                current_expr = None
                last_expr = keepers[-1]
                for repl_arg in keepers[:-1]:
                    current_expr = op(start, repl_arg)
                    start = current_expr
                top_expr = op(start, last_expr)
            else:
                top_expr = replacement

            expr = expr.subs(expr, top_expr)

    return expr


def _simplify_flavors_in_condition(base: str, flavors, expr):
    ''' Simplify conditions based on the knownledge of which flavors
        belong to which OS. '''
    base_expr = simplify_logic(base)
    false_expr = simplify_logic('false')
    for flavor in flavors:
        flavor_expr = simplify_logic(flavor)
        expr = _simplify_expressions(expr, And, (base_expr, flavor_expr,),
                                     flavor_expr)
        expr = _simplify_expressions(expr, Or, (base_expr, flavor_expr),
                                     base_expr)
        expr = _simplify_expressions(expr, And, (Not(base_expr), flavor_expr,),
                                     false_expr)
    return expr


def _simplify_os_families(expr, family_members, other_family_members):
    for family in family_members:
        for other in other_family_members:
            if other in family_members:
                continue  # skip those in the sub-family

            f_expr = simplify_logic(family)
            o_expr = simplify_logic(other)

            expr = _simplify_expressions(expr, And, (f_expr, Not(o_expr)), f_expr)
            expr = _simplify_expressions(expr, And, (Not(f_expr), o_expr), o_expr)
            expr = _simplify_expressions(expr, And, (f_expr, o_expr), simplify_logic('false'))
    return expr


def _recursive_simplify(expr):
    ''' Simplify the expression as much as possible based on
        domain knowledge. '''
    input_expr = expr

    # Simplify even further, based on domain knowledge:
    windowses = ('WIN32', 'WINRT')
    apples = ('APPLE_OSX', 'APPLE_UIKIT', 'APPLE_IOS',
              'APPLE_TVOS', 'APPLE_WATCHOS',)
    bsds = ('FREEBSD', 'OPENBSD', 'NETBSD',)
    androids = ('ANDROID', 'ANDROID_EMBEDDED')
    unixes = ('APPLE', *apples, 'BSD', *bsds, 'LINUX',
              *androids, 'HAIKU',
              'INTEGRITY', 'VXWORKS', 'QNX', 'WASM')

    unix_expr = simplify_logic('UNIX')
    win_expr = simplify_logic('WIN32')
    false_expr = simplify_logic('false')
    true_expr = simplify_logic('true')

    expr = expr.subs(Not(unix_expr), win_expr)  # NOT UNIX -> WIN32
    expr = expr.subs(Not(win_expr), unix_expr)  # NOT WIN32 -> UNIX

    # UNIX [OR foo ]OR WIN32 -> ON [OR foo]
    expr = _simplify_expressions(expr, Or, (unix_expr, win_expr,), true_expr)
    # UNIX  [AND foo ]AND WIN32 -> OFF [AND foo]
    expr = _simplify_expressions(expr, And, (unix_expr, win_expr,), false_expr)

    expr = _simplify_flavors_in_condition('WIN32', ('WINRT',), expr)
    expr = _simplify_flavors_in_condition('APPLE', apples, expr)
    expr = _simplify_flavors_in_condition('BSD', bsds, expr)
    expr = _simplify_flavors_in_condition('UNIX', unixes, expr)
    expr = _simplify_flavors_in_condition('ANDROID', ('ANDROID_EMBEDDED',), expr)

    # Simplify families of OSes against other families:
    expr = _simplify_os_families(expr, ('WIN32', 'WINRT'), unixes)
    expr = _simplify_os_families(expr, androids, unixes)
    expr = _simplify_os_families(expr, ('BSD', *bsds), unixes)

    for family in ('HAIKU', 'QNX', 'INTEGRITY', 'LINUX', 'VXWORKS'):
        expr = _simplify_os_families(expr, (family,), unixes)

    # Now simplify further:
    expr = simplify_logic(expr)

    while expr != input_expr:
        input_expr = expr
        expr = _recursive_simplify(expr)

    return expr


def simplify_condition(condition: str) -> str:
    input_condition = condition.strip()

    # Map to sympy syntax:
    condition = ' ' + input_condition + ' '
    condition = condition.replace('(', ' ( ')
    condition = condition.replace(')', ' ) ')

    tmp = ''
    while tmp != condition:
        tmp = condition

        condition = condition.replace(' NOT ', ' ~ ')
        condition = condition.replace(' AND ', ' & ')
        condition = condition.replace(' OR ', ' | ')
        condition = condition.replace(' ON ', ' true ')
        condition = condition.replace(' OFF ', ' false ')

    try:
        # Generate and simplify condition using sympy:
        condition_expr = simplify_logic(condition)
        condition = str(_recursive_simplify(condition_expr))

        # Map back to CMake syntax:
        condition = condition.replace('~', 'NOT ')
        condition = condition.replace('&', 'AND')
        condition = condition.replace('|', 'OR')
        condition = condition.replace('True', 'ON')
        condition = condition.replace('False', 'OFF')
    except:
        # sympy did not like our input, so leave this condition alone:
        condition = input_condition

    return condition or 'ON'


def recursive_evaluate_scope(scope: Scope, parent_condition: str = '',
                             previous_condition: str = '') -> str:
    current_condition = scope.condition
    total_condition = current_condition
    if total_condition == 'else':
        assert previous_condition, \
            "Else branch without previous condition in: %s" % scope.file
        total_condition = 'NOT ({})'.format(previous_condition)
    if parent_condition:
        if not total_condition:
            total_condition = parent_condition
        else:
            total_condition = '({}) AND ({})'.format(parent_condition,
                                                     total_condition)

    scope.total_condition = simplify_condition(total_condition)

    prev_condition = ''
    for c in scope.children:
        prev_condition = recursive_evaluate_scope(c, total_condition,
                                                  prev_condition)

    return current_condition


def map_to_cmake_condition(condition: str) -> str:
    condition = re.sub(r'\bQT_ARCH___equals___([a-zA-Z_0-9]*)',
                       r'(TEST_architecture_arch STREQUAL "\1")', condition)
    condition = re.sub(r'\bQT_ARCH___contains___([a-zA-Z_0-9]*)',
                       r'(TEST_architecture_arch STREQUAL "\1")', condition)
    return condition


def write_resources(cm_fh: typing.IO[str], target: str, scope: Scope, indent: int = 0):
    vpath = scope.expand('VPATH')

    # Handle QRC files by turning them into add_qt_resource:
    resources = scope.get_files('RESOURCES')
    qrc_output = ''
    if resources:
        qrc_only = True
        for r in resources:
            if r.endswith('.qrc'):
                qrc_output += process_qrc_file(target, r, scope.basedir)
            else:
                qrc_only = False

        if not qrc_only:
            print('     XXXX Ignoring non-QRC file resources.')

    if qrc_output:
        cm_fh.write('\n# Resources:\n')
        for line in qrc_output.split('\n'):
            cm_fh.write(' ' * indent + line + '\n')


def write_extend_target(cm_fh: typing.IO[str], target: str,
                        scope: Scope, indent: int = 0):
    ind = spaces(indent)
    extend_qt_io_string = io.StringIO()
    write_sources_section(extend_qt_io_string, scope)
    extend_qt_string = extend_qt_io_string.getvalue()

    extend_scope = '\n{}extend_target({} CONDITION {}\n' \
                   '{}{})\n'.format(ind, target,
                                    map_to_cmake_condition(scope.total_condition),
                                    extend_qt_string, ind)

    if not extend_qt_string:
        extend_scope = ''  # Nothing to report, so don't!

    cm_fh.write(extend_scope)

    write_resources(cm_fh, target, scope, indent)


def flatten_scopes(scope: Scope) -> typing.List[Scope]:
    result = [scope]  # type: typing.List[Scope]
    for c in scope.children:
        result += flatten_scopes(c)
    return result


def merge_scopes(scopes: typing.List[Scope]) -> typing.List[Scope]:
    result = []  # type: typing.List[Scope]

    # Merge scopes with their parents:
    known_scopes = {}  # type: typing.Mapping[str, Scope]
    for scope in scopes:
        total_condition = scope.total_condition
        if total_condition == 'OFF':
            # ignore this scope entirely!
            pass
        elif total_condition in known_scopes:
            known_scopes[total_condition].merge(scope)
        else:
            # Keep everything else:
            result.append(scope)
            known_scopes[total_condition] = scope

    return result


def write_simd_part(cm_fh: typing.IO[str], target: str, scope: Scope, indent: int = 0):
    simd_options = [ 'sse2', 'sse3', 'ssse3', 'sse4_1', 'sse4_2', 'aesni', 'shani', 'avx', 'avx2',
                     'avx512f', 'avx512cd', 'avx512er', 'avx512pf', 'avx512dq', 'avx512bw',
                     'avx512vl', 'avx512ifma', 'avx512vbmi', 'f16c', 'rdrnd', 'neon', 'mips_dsp',
                     'mips_dspr2',
                     'arch_haswell', 'avx512common', 'avx512core'];
    ind = spaces(indent)

    for simd in simd_options:
        SIMD = simd.upper();
        write_source_file_list(cm_fh, scope, 'SOURCES',
                           ['{}_HEADERS'.format(SIMD),
                            '{}_SOURCES'.format(SIMD),
                            '{}_C_SOURCES'.format(SIMD),
                            '{}_ASM'.format(SIMD)],
                           indent,
                           header = '{}add_qt_simd_part({} SIMD {}\n'.format(ind, target, simd),
                           footer = '{})\n\n'.format(ind))


def write_main_part(cm_fh: typing.IO[str], name: str, typename: str,
                    cmake_function: str, scope: Scope, *,
                    extra_lines: typing.List[str] = [],
                    indent: int = 0, extra_keys: typing.List[str],
                    **kwargs: typing.Any):
    # Evaluate total condition of all scopes:
    recursive_evaluate_scope(scope)

    # Get a flat list of all scopes but the main one:
    scopes = flatten_scopes(scope)
    total_scopes = len(scopes)
    # Merge scopes based on their conditions:
    scopes = merge_scopes(scopes)

    assert len(scopes)
    assert scopes[0].total_condition == 'ON'

    scopes[0].reset_visited_keys()
    for k in extra_keys:
        scopes[0].get(k)

    # Now write out the scopes:
    write_header(cm_fh, name, typename, indent=indent)

    cm_fh.write('{}{}({}\n'.format(spaces(indent), cmake_function, name))
    for extra_line in extra_lines:
        cm_fh.write('{}    {}\n'.format(spaces(indent), extra_line))

    write_sources_section(cm_fh, scopes[0], indent=indent, **kwargs)

    # Footer:
    cm_fh.write('{})\n'.format(spaces(indent)))

    write_resources(cm_fh, name, scope, indent)

    write_simd_part(cm_fh, name, scope, indent)

    ignored_keys_report = write_ignored_keys(scopes[0], spaces(indent))
    if ignored_keys_report:
        cm_fh.write(ignored_keys_report)


    # Scopes:
    if len(scopes) == 1:
        return

    write_scope_header(cm_fh, indent=indent)

    for c in scopes[1:]:
        c.reset_visited_keys()
        write_extend_target(cm_fh, name, c, indent=indent)
        ignored_keys_report = write_ignored_keys(c, spaces(indent))
        if ignored_keys_report:
            cm_fh.write(ignored_keys_report)


def write_module(cm_fh: typing.IO[str], scope: Scope, *,
                 indent: int = 0) -> None:
    module_name = scope.TARGET
    if not module_name.startswith('Qt'):
        print('XXXXXX Module name {} does not start with Qt!'.format(module_name))

    extra = []
    if 'static' in scope.get('CONFIG'):
        extra.append('STATIC')
    if 'no_module_headers' in scope.get('CONFIG'):
        extra.append('NO_MODULE_HEADERS')

    write_main_part(cm_fh, module_name[2:], 'Module', 'add_qt_module', scope,
                    extra_lines=extra, indent=indent,
                    known_libraries={'Qt::Core', }, extra_keys=[])

    if 'qt_tracepoints' in scope.get('CONFIG'):
        tracepoints = scope.get_files('TRACEPOINT_PROVIDER')
        cm_fh.write('\n\n{}qt_create_tracepoints({} {})\n'
                    .format(spaces(indent), module_name[2:], ' '.join(tracepoints)))


def write_tool(cm_fh: typing.IO[str], scope: Scope, *,
               indent: int = 0) -> None:
    tool_name = scope.TARGET

    extra = ['BOOTSTRAP'] if 'force_bootstrap' in scope.get('CONFIG', []) else []

    write_main_part(cm_fh, tool_name, 'Tool', 'add_qt_tool', scope,
                    indent=indent, known_libraries={'Qt::Core', },
                    extra_lines=extra, extra_keys=['CONFIG'])


def write_test(cm_fh: typing.IO[str], scope: Scope, *,
               indent: int = 0) -> None:
    test_name = scope.TARGET
    assert test_name

    write_main_part(cm_fh, test_name, 'Test', 'add_qt_test', scope,
                    indent=indent, known_libraries={'Qt::Core', 'Qt::Test',},
                    extra_keys=[])


def write_binary(cm_fh: typing.IO[str], scope: Scope,
                 gui: bool = False, *, indent: int = 0) -> None:
    binary_name = scope.TARGET
    assert binary_name

    extra = ['GUI',] if gui else[]

    target_path = scope.get_string('target.path')
    if target_path:
        target_path = target_path.replace('$$[QT_INSTALL_EXAMPLES]', '${INSTALL_EXAMPLESDIR}')
        extra.append('OUTPUT_DIRECTORY "{}"'.format(target_path))
        if 'target' in scope.get('INSTALLS'):
            extra.append('INSTALL_DIRECTORY "{}"'.format(target_path))

    write_main_part(cm_fh, binary_name, 'Binary', 'add_qt_executable', scope,
                    extra_lines=extra, indent=indent,
                    known_libraries={'Qt::Core', }, extra_keys=['target.path', 'INSTALLS'])


def write_plugin(cm_fh, scope, *, indent: int = 0):
    plugin_name = scope.TARGET
    assert plugin_name

    write_main_part(cm_fh, plugin_name, 'Plugin', 'add_qt_plugin', scope,
                    indent=indent, known_libraries={'QtCore', }, extra_keys=[])


def handle_app_or_lib(scope: Scope, cm_fh: typing.IO[str], *,
                      indent: int = 0) -> None:
    assert scope.TEMPLATE in ('app', 'lib')

    is_lib = scope.TEMPLATE == 'lib'
    is_plugin = any('qt_plugin' == s for s in scope.get('_LOADED'))

    if is_lib or 'qt_module' in scope.get('_LOADED'):
        write_module(cm_fh, scope, indent=indent)
    elif is_plugin:
        write_plugin(cm_fh, scope, indent=indent)
    elif 'qt_tool' in scope.get('_LOADED'):
        write_tool(cm_fh, scope, indent=indent)
    else:
        if 'testcase' in scope.get('CONFIG') \
                or 'testlib' in scope.get('CONFIG'):
            write_test(cm_fh, scope, indent=indent)
        else:
            gui = 'console' not in scope.get('CONFIG')
            write_binary(cm_fh, scope, gui, indent=indent)

    ind = spaces(indent)
    write_source_file_list(cm_fh, scope, '',
                           ['QMAKE_DOCS',],
                           indent,
                           header = '{}add_qt_docs(\n'.format(ind),
                           footer = '{})\n'.format(ind))


def cmakeify_scope(scope: Scope, cm_fh: typing.IO[str], *,
                   indent: int = 0) -> None:
    template = scope.TEMPLATE
    if template == 'subdirs':
        handle_subdir(scope, cm_fh, indent=indent)
    elif template in ('app', 'lib'):
        handle_app_or_lib(scope, cm_fh, indent=indent)
    else:
        print('    XXXX: {}: Template type {} not yet supported.'
              .format(scope.file, template))


def generate_cmakelists(scope: Scope) -> None:
    with open(scope.cMakeListsFile, 'w') as cm_fh:
        assert scope.file
        cm_fh.write('# Generated from {}.\n\n'
                    .format(os.path.basename(scope.file)))
        cmakeify_scope(scope, cm_fh)


def do_include(scope: Scope, *, debug: bool = False) -> None:
    for c in scope.children:
        do_include(c)

    for include_file in scope.get_files('_INCLUDED', is_include=True):
        if not include_file:
            continue
        if not os.path.isfile(include_file):
            print('    XXXX: Failed to include {}.'.format(include_file))
            continue

        include_result = parseProFile(include_file, debug=debug)
        include_scope \
            = Scope.FromDict(None, include_file,
                             include_result.asDict().get('statements'),
                             '', scope.basedir)  # This scope will be merged into scope!

        do_include(include_scope)

        scope.merge(include_scope)


def main() -> None:
    args = _parse_commandline()

    debug_parsing = args.debug_parser or args.debug

    for file in args.files:
        parseresult = parseProFile(file, debug=debug_parsing)

        if args.debug_parse_result or args.debug:
            print('\n\n#### Parser result:')
            print(parseresult)
            print('\n#### End of parser result.\n')
        if args.debug_parse_dictionary or args.debug:
            print('\n\n####Parser result dictionary:')
            print(parseresult.asDict())
            print('\n#### End of parser result dictionary.\n')

        file_scope = Scope.FromDict(None, file,
                                    parseresult.asDict().get('statements'))

        if args.debug_pro_structure or args.debug:
            print('\n\n#### .pro/.pri file structure:')
            print(file_scope.dump())
            print('\n#### End of .pro/.pri file structure.\n')

        do_include(file_scope, debug=debug_parsing)

        if args.debug_full_pro_structure or args.debug:
            print('\n\n#### Full .pro/.pri file structure:')
            print(file_scope.dump())
            print('\n#### End of full .pro/.pri file structure.\n')

        generate_cmakelists(file_scope)


if __name__ == '__main__':
    main()