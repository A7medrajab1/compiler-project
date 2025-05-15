import re

class Scanner:
    def __init__(self):
        self.keywords = {
            'IfTrue-Otherwise': 'Condition',
            'IfTrue': 'If', 'Otherwise': 'Else',
            'Imw': 'Integer', 'SIMw': 'SInteger',
            'Chj': 'Character', 'Series': 'String',
            'IMwf': 'Float', 'SIMwf': 'SFloat',
            'NOReturn': 'Void', 'RepeatWhen': 'Loop',
            'Reiterate': 'Loop', 'Turnback': 'Return',
            'OutLoop': 'Break', 'Loli': 'Struct',
            'include': 'Include', 'Stop': 'Break',
            'int': 'Type'
        }

        self.symbols = {
            '+': 'Plus', '-': 'Minus', '*': 'Mult', '/': 'Div', '=': 'Assignment operator',
            '==': 'Equal', '!=': 'Not Equal', '<': 'Less Than', '<=': 'Less Than or Equal',
            '>': 'Greater Than', '>=': 'Greater Than or Equal', '&&': 'And', '||': 'Or', '~': 'Not',
            '(': 'Braces', ')': 'Braces', '{': 'Braces', '}': 'Braces', '[': 'Braces', ']': 'Braces',
            ';': 'Semicolon', ':': 'Colon', ',': 'Comma', '->': 'Access Operator'
        }

        # Token patterns (ordered for priority)
        self.token_patterns = [
            (re.compile(r'"[^"]*"'), 'String Literal'),
            (re.compile(r"'[^']*'"), 'Character Literal'),
            (re.compile(r'\d+\.\d+'), 'Float Number'),
            (re.compile(r'\d+'), 'Constant'),
            (re.compile(r'[A-Za-z_][A-Za-z0-9_\-]*'), 'Identifier')
        ]

        self.invalid_id_pattern = re.compile(r'\d+[A-Za-z_][A-Za-z0-9_]*')
        self.comment_start = re.compile(r'/@')
        self.comment_end = re.compile(r'@/')
        self.symbol_regex = re.compile(
            '|'.join(re.escape(sym) for sym in sorted(self.symbols, key=len, reverse=True))
        )

    def tokenize_line(self, line, line_number):
        tokens = []
        errors = []

        pos = 0
        while pos < len(line):
            if line[pos].isspace():
                pos += 1
                continue

            # Invalid identifiers
            match = self.invalid_id_pattern.match(line, pos)
            if match:
                invalid = match.group()
                errors.append((line_number, invalid, 'Invalid Identifier'))
                pos += len(invalid)
                continue

            # Symbols
            match = self.symbol_regex.match(line, pos)
            if match:
                symbol = match.group()
                tokens.append((line_number, symbol, self.symbols[symbol]))
                pos += len(symbol)
                continue

            # Keywords, identifiers, numbers, strings
            matched = False
            for pattern, token_type in self.token_patterns:
                match = pattern.match(line, pos)
                if match:
                    val = match.group()
                    if token_type == 'Identifier' and val in self.keywords:
                        tokens.append((line_number, val, self.keywords[val]))
                    else:
                        tokens.append((line_number, val, token_type))
                    pos += len(val)
                    matched = True
                    break
            if matched:
                continue

            # Unknown token
            errors.append((line_number, line[pos], 'Unknown Token'))
            pos += 1

        return tokens, errors

    def tokenize(self, code):
        lines = code.split('\n')
        tokens, errors = [], []
        in_comment = False

        for i, line in enumerate(lines, 1):
            if in_comment:
                end_match = self.comment_end.search(line)
                if end_match:
                    content = line[:end_match.start()].strip()
                    if content:
                        tokens.append((i, content, 'Comment Content'))
                    tokens.append((i, '@/','Comment End'))
                    remainder = line[end_match.end():].strip()
                    if remainder:
                        t, e = self.tokenize_line(remainder, i)
                        tokens.extend(t)
                        errors.extend(e)
                    in_comment = False
                else:
                    if line.strip():
                        tokens.append((i, line.strip(), 'Comment Content'))
                continue

            start_match = self.comment_start.search(line)
            end_match = self.comment_end.search(line)

            if start_match and end_match and start_match.start() < end_match.start():
                before = line[:start_match.start()].strip()
                if before:
                    t, e = self.tokenize_line(before, i)
                    tokens.extend(t)
                    errors.extend(e)
                tokens.append((i, '/@', 'Comment Start'))
                content = line[start_match.end():end_match.start()].strip()
                if content:
                    tokens.append((i, content, 'Comment Content'))
                tokens.append((i, '@/', 'Comment End'))
                after = line[end_match.end():].strip()
                if after:
                    t, e = self.tokenize_line(after, i)
                    tokens.extend(t)
                    errors.extend(e)
            elif start_match:
                before = line[:start_match.start()].strip()
                if before:
                    t, e = self.tokenize_line(before, i)
                    tokens.extend(t)
                    errors.extend(e)
                tokens.append((i, '/@', 'Comment Start'))
                content = line[start_match.end():].strip()
                if content:
                    tokens.append((i, content, 'Comment Content'))
                in_comment = True
            else:
                t, e = self.tokenize_line(line, i)
                tokens.extend(t)
                errors.extend(e)

        return tokens, errors

    def print_tokens(self, tokens, errors):
        print("Scanner Output:")
        for token in tokens:
            print(f"Line : {token[0]} Token Text: {token[1]}   Token Type: {token[2]}")
        for error in errors:
            print(f"Line : {error[0]} Error in Token Text: {error[1]}   Token Type: {error[2]}")
        print(f"Total NO of errors: {len(errors)}")
        print("-" * 30)
