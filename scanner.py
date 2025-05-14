import re
import os

class Scanner:
    def __init__(self):
        self.keywords = {
            'IfTrue-Otherwise': 'Condition',
            'IfTrue': 'If',
            'Otherwise': 'Else',
            'Imw': 'Integer',
            'SIMw': 'SInteger',
            'Chj': 'Character',
            'Series': 'String',
            'IMwf': 'Float',
            'SIMwf': 'SFloat',
            'NOReturn': 'Void',
            'RepeatWhen': 'Loop',
            'Reiterate': 'Loop',
            'Turnback': 'Return',
            'OutLoop': 'Break',
            'Loli': 'Struct',
            'Include': 'Inclusion',
            'Stop': 'Break',
            'int': 'Type'
        }
        self.symbols = {
            '+': 'Plus', 
            '-': 'Minus', 
            '*': 'Mult', 
            '/': 'Div',
            '=': 'Assignment operator',
            '==': 'Equal', 
            '!=': 'Not Equal', 
            '<': 'Less Than', 
            '<=': 'Less Than or Equal', 
            '>': 'Greater Than', 
            '>=': 'Greater Than or Equal',
            '&&': 'And', 
            '||': 'Or', 
            '~': 'Not',
            '(': 'Braces', 
            ')': 'Braces',
            '{': 'Braces', 
            '}': 'Braces',
            '[': 'Braces', 
            ']': 'Braces',
            ';': 'Semicolon', 
            ':': 'Colon', 
            ',': 'Comma',
            '->': 'Access Operator'
        }
        self.token_patterns = [
            (r'"[^"]*"', 'String Literal'),
            (r"'[^']*'", 'Character Literal'),
            (r'\d+\.\d+', 'Float Number'),
            (r'\d+', 'Constant'),
            (r'[A-Za-z_][A-Za-z0-9_\-]*', 'Identifier'),
        ]
        self.invalid_id_pattern = re.compile(r'\d+[A-Za-z_][A-Za-z0-9_]*')
        self.single_line_comment = re.compile(r'/\^.*')
        self.symbol_pattern = '|'.join(re.escape(s) for s in sorted(self.symbols.keys(), key=lambda x: -len(x)))

    def tokenize_line(self, line, line_number, included_files=None):
        tokens = []
        errors = []

        i = 0
        while i < len(line):
            if line[i].isspace():
                i += 1
                continue

            # Invalid identifier starting with digit (every occurrence is an error)
            invalid_match = re.match(r'\d+[A-Za-z_][A-Za-z0-9_]*', line[i:])
            if invalid_match:
                invalid_id = invalid_match.group(0)
                errors.append((line_number, invalid_id, 'Invalid Identifier'))  # NO DEDUPLICATION
                i += len(invalid_id)
                continue

            # Symbols
            symbol_found = False
            for symbol in sorted(self.symbols.keys(), key=len, reverse=True):
                if line[i:].startswith(symbol):
                    tokens.append((line_number, symbol, self.symbols[symbol]))
                    i += len(symbol)
                    symbol_found = True
                    break
            if symbol_found:
                continue

            # Token patterns
            token_match = False
            for pattern, token_type in self.token_patterns:
                match = re.match(pattern, line[i:])
                if match:
                    token = match.group(0)
                    if token_type == 'Identifier' and token in self.keywords:
                        tokens.append((line_number, token, self.keywords[token]))
                    else:
                        tokens.append((line_number, token, token_type))
                    i += len(token)
                    token_match = True
                    break
            if token_match:
                continue

            # Unknown token
            unknown_token = line[i]
            errors.append((line_number, unknown_token, 'Unknown Token'))
            i += 1

        return tokens, errors

    def tokenize(self, code, included_files=None):
        if included_files is None:
            included_files = []
        lines = code.split('\n')
        all_tokens = []
        all_errors = []
        in_comment = False

        for i, line in enumerate(lines, 1):
            line_strip = line.strip()
            start_idx = line.find('/@')
            end_idx = line.find('@/')
            if not in_comment and start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                all_tokens.append((i, '/@', 'Comment Start'))
                content = line[start_idx + 2:end_idx]
                if content.strip():
                    all_tokens.append((i, content.strip(), 'Comment Content'))
                all_tokens.append((i, '@/','Comment End'))
                before = line[:start_idx].strip()
                after = line[end_idx+2:].strip()
                if before:
                    tokens, errors = self.tokenize_line(before, i, included_files)
                    all_tokens.extend(tokens)
                    all_errors.extend(errors)
                if after:
                    tokens, errors = self.tokenize_line(after, i, included_files)
                    all_tokens.extend(tokens)
                    all_errors.extend(errors)
                continue
            if not in_comment and start_idx != -1:
                in_comment = True
                all_tokens.append((i, '/@', 'Comment Start'))
                content = line[start_idx + 2:]
                if content.strip():
                    all_tokens.append((i, content.strip(), 'Comment Content'))
                before = line[:start_idx].strip()
                if before:
                    tokens, errors = self.tokenize_line(before, i, included_files)
                    all_tokens.extend(tokens)
                    all_errors.extend(errors)
                continue
            if in_comment and end_idx != -1:
                content = line[:end_idx].strip()
                if content:
                    all_tokens.append((i, content, 'Comment Content'))
                all_tokens.append((i, '@/','Comment End'))
                after = line[end_idx+2:].strip()
                if after:
                    tokens, errors = self.tokenize_line(after, i, included_files)
                    all_tokens.extend(tokens)
                    all_errors.extend(errors)
                in_comment = False
                continue
            if in_comment:
                if line_strip:
                    all_tokens.append((i, line_strip, 'Comment Content'))
                continue
            tokens, errors = self.tokenize_line(line, i, included_files)
            all_tokens.extend(tokens)
            all_errors.extend(errors)
        return all_tokens, all_errors

    def print_tokens(self, tokens, errors):
        print("Scanner Output:")
        for token in tokens:
            print(f"Line : {token[0]} Token Text: {token[1]}   Token Type: {token[2]}")
        for error in errors:
            print(f"Line : {error[0]} Error in Token Text: {error[1]}   Token Type: {error[2]}")
        print(f"Total NO of errors: {len(errors)}")
        print("-" * 29)