class Parser:
    """
    Recursive-descent parser for custom language grammar.
    `tokens` is a list of (line, text, type).
    `scanner_errors` is a list of (line, text, "Invalid Identifier").
    """

    TYPE_SPECIFIERS = {
        'Integer', 'SInteger', 'Character', 'String',
        'Float', 'SFloat', 'Void', 'Type',
    }

    def __init__(self, tokens, scanner_errors):
        self.tokens = tokens
        self.current = 0
        self.errors = []
        self.matched_rules = []

        # Index scanner errors by line for quick lookup
        self.scanner_errors = {}
        for line, txt, _ in scanner_errors:
            self.scanner_errors.setdefault(line, []).append(txt)

    def peek(self):
        return self.tokens[self.current] if self.current < len(self.tokens) else None

    def advance(self):
        self.current += 1

    def consume(self, typ=None, val=None):
        tok = self.peek()
        if not tok:
            return False
        if typ and tok[2] != typ:
            return False
        if val and tok[1] != val:
            return False
        self.advance()
        return True

    def parse(self):
        self.parse_program()
        # Report any leftover scanner errors
        for line, txt_list in self.scanner_errors.items():
            for txt in txt_list:
                self.errors.append((line, f'Invalid identifier "{txt}"'))

    #
    # Program → declaration-list | comment | include_command
    #
    def parse_program(self):
        while self.current < len(self.tokens):
            tok = self.peek()
            if not tok:
                break
            line = tok[0]

            # Skip stray top-level closing braces
            if tok[1] == '}' and tok[2] == 'Braces':
                self.advance()
                continue

            # Report and skip scanner errors on this line
            if line in self.scanner_errors:
                for txt in self.scanner_errors.pop(line):
                    self.errors.append((line, f'Invalid identifier "{txt}"'))
                self.advance()
                continue

            # Try all possible top-level constructs in priority order
            if self.try_comment():
                self.matched_rules.append((line, 'comment'))
                continue

            if self.try_include():
                self.matched_rules.append((line, 'include_command'))
                continue

            if self.try_fun_declaration():
                self.matched_rules.append((line, 'fun-declaration'))
                continue

            if self.try_var_declaration():
                self.matched_rules.append((line, 'var-declaration'))
                continue

            # Unexpected token fallback
            self.errors.append((line, f'Unexpected token "{tok[1]}"'))
            self.advance()

    #
    # Var Declaration → type-specifier Identifier ;
    #
    def try_var_declaration(self):
        start = self.current
        if self.try_type_specifier() and self.consume('Identifier') and self.consume('Semicolon'):
            return True
        self.current = start
        return False

    #
    # Type Specifier → one of TYPE_SPECIFIERS
    #
    def try_type_specifier(self):
        tok = self.peek()
        if tok and tok[2] in self.TYPE_SPECIFIERS:
            self.advance()
            return True
        return False

    #
    # Fun Declaration → type-specifier Identifier ( params ) compound-stmt
    #
    def try_fun_declaration(self):
        start = self.current
        if (self.try_type_specifier() and
            self.consume('Identifier') and
            self.consume('Braces', '(')):
            self.parse_params()
            if self.consume('Braces', ')') and self.try_compound_stmt():
                return True
        self.current = start
        return False

    #
    # Params and Param List
    #
    def parse_params(self):
        # NOReturn or empty params
        if self.consume('NOReturn'):
            return
        if not self.parse_param():
            return
        while self.consume('Comma'):
            if not self.parse_param():
                break

    def parse_param(self):
        start = self.current
        if self.try_type_specifier() and self.consume('Identifier'):
            return True
        self.current = start
        return False

    #
    # Compound Statement → { local-declarations statement-list }
    #
    def try_compound_stmt(self):
        start = self.current
        if not self.consume('Braces', '{'):
            return False

        while self.current < len(self.tokens):
            tok = self.peek()
            if tok and tok[1] == '}' and tok[2] == 'Braces':
                break
            line = tok[0] if tok else -1

            # Handle nested scanner errors
            if line in self.scanner_errors:
                for txt in self.scanner_errors.pop(line):
                    self.errors.append((line, f'Invalid identifier "{txt}"'))
                self.advance()
                continue

            # Try nested constructs inside block
            if self.try_comment():
                self.matched_rules.append((line, 'comment'))
                continue
            if self.try_var_declaration():
                self.matched_rules.append((line, 'var-declaration'))
                continue
            if self.try_iteration_stmt():
                self.matched_rules.append((line, 'iteration-stmt'))
                continue
            if self.try_selection_stmt():
                self.matched_rules.append((line, 'selection-stmt'))
                continue
            if self.try_jump_stmt():
                self.matched_rules.append((line, 'jump-stmt'))
                continue
            if self.try_expression_stmt():
                self.matched_rules.append((line, 'expression-stmt'))
                continue

            self.advance()  # fallback advance

        # Consume closing brace
        if self.consume('Braces', '}'):
            return True
        self.current = start
        return False

    #
    # Expression Statement → expression ; | ;
    #
    def try_expression_stmt(self):
        start = self.current
        if self.consume('Semicolon'):
            return True
        if self.parse_expression() and self.consume('Semicolon'):
            return True
        self.current = start
        return False

    #
    # Selection Statement → IfTrue ( expression ) statement [ Otherwise statement ]
    #
    def try_selection_stmt(self):
        start = self.current
        if (self.consume('IfTrue') and
            self.consume('Braces', '(') and
            self.parse_expression() and
            self.consume('Braces', ')') and
            self.try_compound_stmt()):
            if self.consume('Otherwise'):
                self.try_compound_stmt()
            return True
        self.current = start
        return False

    #
    # Iteration Statement → RepeatWhen or Reiterate loop
    #
    def try_iteration_stmt(self):
        start = self.current
        if (self.consume('Loop', 'RepeatWhen') and
            self.consume('Braces', '(') and
            self.parse_expression() and
            self.consume('Braces', ')') and
            self.try_compound_stmt()):
            return True

        self.current = start
        if (self.consume('Reiterate') and
            self.consume('Braces', '(') and
            self.parse_expression() and
            self.consume('Semicolon') and
            self.parse_expression() and
            self.consume('Semicolon') and
            self.parse_expression() and
            self.consume('Braces', ')') and
            self.try_compound_stmt()):
            return True

        self.current = start
        return False

    #
    # Jump Statement → Turnback expression ; | Stop ;
    #
    def try_jump_stmt(self):
        start = self.current
        if self.consume('Turnback') and self.parse_expression() and self.consume('Semicolon'):
            return True
        if self.consume('Stop') and self.consume('Semicolon'):
            return True
        self.current = start
        return False

    #
    # Expression Parsing
    #
    def parse_expression(self):
        start = self.current
        # Assignment: Identifier '=' expression
        if self.peek() and self.peek()[2] == 'Identifier':
            self.advance()
            if self.consume('Assignment operator') and self.parse_expression():
                return True
            self.current = start  # rollback if not assignment

        # Else parse as simple-expression
        return self.parse_simple_expression()

    def parse_simple_expression(self):
        start = self.current
        if not self.parse_additive_expression():
            return False

        tok = self.peek()
        if tok and tok[1] in {'<','<=','>','>=','==','!=','&&','||'}:
            self.advance()
            if not self.parse_additive_expression():
                self.current = start
                return False
        return True

    def parse_additive_expression(self):
        if not self.parse_term():
            return False
        while True:
            tok = self.peek()
            if not tok or tok[1] not in {'+', '-'}:
                break
            self.advance()
            if not self.parse_term():
                return False
        return True

    def parse_term(self):
        if not self.parse_factor():
            return False
        while True:
            tok = self.peek()
            if not tok or tok[1] not in {'*', '/'}:
                break
            self.advance()
            if not self.parse_factor():
                return False
        return True

    def parse_factor(self):
        # Parenthesized expression
        if self.consume('Braces', '('):
            if not self.parse_expression():
                return False
            if not self.consume('Braces', ')'):
                return False
            return True

        # Identifier or function call
        if self.consume('Identifier'):
            if self.consume('Braces', '('):
                self.parse_args()
                self.consume('Braces', ')')
            return True

        # Number or constant
        return self.parse_num()

    #
    # Function call arguments
    #
    def parse_args(self):
        if self.peek() and self.peek()[1] == ')' and self.peek()[2] == 'Braces':
            return
        self.parse_arg_list()

    def parse_arg_list(self):
        if not self.parse_expression():
            return False
        while self.consume('Comma') and self.parse_expression():
            pass
        return True

    #
    # Numeric constants and values
    #
    def parse_num(self):
        tok = self.peek()
        if tok and tok[1] in ('+', '-'):
            self.advance()
            return self.parse_value()
        return self.parse_value()

    def parse_value(self):
        return self.consume('Constant')

    #
    # Include command → include ( "filename.txt" );
    #
    def try_include(self):
        start = self.current
        if not self.consume('Include'):
            return False
        line = self.peek()[0] if self.peek() else -1

        if not self.consume('Braces', '('):
            self.record_unexpected_token(line)
            self.current = start
            return False

        if not self.consume('String Literal'):
            self.record_unexpected_token(line, missing='file string')
            self.current = start
            return False

        if not self.consume('Braces', ')'):
            self.record_unexpected_token(line)
            self.current = start
            return False

        if not self.consume('Semicolon'):
            self.record_unexpected_token(line)
            self.current = start
            return False

        return True

    def record_unexpected_token(self, line, missing=None):
        tok = self.peek()
        if missing:
            msg = f'Missing {missing}'
        elif tok:
            msg = f'Unexpected token "{tok[1]}"'
        else:
            msg = 'Unexpected end of input'
        self.errors.append((line, msg))

    #
    # Comment → /@ ... @/
    #
    def try_comment(self):
        start = self.current
        if self.consume('Comment Start'):
            while self.consume('Comment Content'):
                pass
            self.consume('Comment End')
            return True
        self.current = start
        return False

    def print_results(self):
        print("\nParser Phase Output:")
        for ln, rule in sorted(self.matched_rules, key=lambda x: x[0]):
            print(f"Line: {ln} Matched Rule: {rule}")
        for ln, msg in sorted(self.errors, key=lambda x: x[0]):
            print(f"Line: {ln} Error: {msg}")
        print(f"\nTotal Errors: {len(self.errors)}")
