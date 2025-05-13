import re
import os

class Scanner:
    def __init__(self):
        # Keywords dictionary
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
            'int': 'Type'  # Added to match the example output
        }
        
        # Symbols with output-friendly names
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
        
        # Token patterns
        self.token_patterns = [
            (r'"[^"]*"', 'String Literal'),
            (r"'[^']*'", 'Character Literal'),
            (r'\d+\.\d+', 'Float Number'),
            (r'\d+', 'Constant'),
            (r'[A-Za-z_][A-Za-z0-9_\-]*', 'Identifier'),
        ]
        
        # Invalid identifier pattern - starts with a digit
        self.invalid_id_pattern = re.compile(r'\d+[A-Za-z_][A-Za-z0-9_]*')
        
        # Comment patterns
        self.single_line_comment = re.compile(r'/\^.*')
        
        # Error count
        self.error_count = 0
        
        # Symbol regex (longest first)
        self.symbol_pattern = '|'.join(re.escape(s) for s in sorted(self.symbols.keys(), key=lambda x: -len(x)))
        
    def tokenize_line(self, line, line_number, included_files=None):
        tokens = []
        errors = []
        
        # Check for include directive at start of line
        if included_files is not None:
            include_match = re.match(r'^Include\s*$$\s*"([^"]+)"\s*$$\s*;', line)
            if include_match:
                filename = include_match.group(1)
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        included_content = f.read()
                    included_tokens, included_errors = self.tokenize(included_content, 
                                                    included_files + [filename])
                    tokens.extend(included_tokens)
                    errors.extend(included_errors)
                    return tokens, errors
        
        # Check for single-line comments
        if self.single_line_comment.match(line):
            tokens.append((line_number, line, 'Comment'))
            return tokens, errors
        
        # Special handling for invalid identifiers (starting with digit)
        invalid_ids = self.invalid_id_pattern.findall(line)
        for invalid_id in invalid_ids:
            errors.append((line_number, invalid_id, 'Invalid Identifier'))
            self.error_count += 1
            # Replace with spaces to avoid further processing
            line = line.replace(invalid_id, ' ' * len(invalid_id))
        
        # Split the line by symbols
        split_pattern = f'({self.symbol_pattern})'
        parts = [p for p in re.split(split_pattern, line) if p]
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            if part in self.symbols:
                tokens.append((line_number, part, self.symbols[part]))
            else:
                matched = False
                for pattern, token_type in self.token_patterns:
                    if re.fullmatch(pattern, part):
                        if token_type == 'Identifier' and part in self.keywords:
                            tokens.append((line_number, part, self.keywords[part]))
                        else:
                            tokens.append((line_number, part, token_type))
                        matched = True
                        break
                if not matched and (line_number, part, 'Invalid Identifier') not in errors:
                    errors.append((line_number, part, 'Unknown Token'))
                    self.error_count += 1
        
        return tokens, errors
        
    def tokenize(self, code, included_files=None):
        if included_files is None:
            included_files = []

        lines = code.split('\n')
        all_tokens = []
        all_errors = []
        in_comment = False
        comment_start_line = 0

        for i, line in enumerate(lines, 1):
            line_strip = line.strip()

            # Check if comment starts and ends on the same line
            start_idx = line.find('/@')
            end_idx = line.find('@/')

            if not in_comment and start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                # Single line multi-line comment
                all_tokens.append((i, '/@', 'Comment Start'))
                content = line[start_idx + 2:end_idx]
                if content.strip():
                    all_tokens.append((i, content.strip(), 'Comment Content'))
                all_tokens.append((i, '@/','Comment End'))
                # Tokenize any code before or after the comment
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

            # Multi-line comment starts
            if not in_comment and start_idx != -1:
                in_comment = True
                comment_start_line = i
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

            # Multi-line comment ends
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

            # Inside multi-line comment
            if in_comment:
                if line_strip:
                    all_tokens.append((i, line_strip, 'Comment Content'))
                continue

            # Process normal line
            tokens, errors = self.tokenize_line(line, i, included_files)
            all_tokens.extend(tokens)
            all_errors.extend(errors)

        # handle unterminated multi-line comments if needed (optional)
        return all_tokens, all_errors
    
    def print_tokens(self, tokens, errors):
        print("Scanner Output:")
        for token in tokens:
            print(f"Line : {token[0]} Token Text: {token[1]}   Token Type: {token[2]}")
        
        for error in errors:
            print(f"Line : {error[0]} Error in Token Text: {error[1]}   Token Type: {error[2]}")
            
        print(f"Total NO of errors: {len(errors)}")
        print("-" * 29)