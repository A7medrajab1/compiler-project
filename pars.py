class Parser:
    # Update type definitions to match scanner output
    TYPES = {'Type', 'Void'}
    
    def __init__(self, tokens, scanner_errors):
        self.tokens = tokens
        self.errors = []
        self.matched_rules = []
        self.current = 0
        self.scanner_errors_by_line = {}
        for line, text, _ in scanner_errors:
            self.scanner_errors_by_line.setdefault(line, []).append(text)

    def parse(self):
        """Parse the entire program"""
        while self.current < len(self.tokens):
            if self.current >= len(self.tokens):
                break
                
            token = self.peek()
            if not token:
                break
                
            line = token[0]
            
            # Handle scanner errors first
            if line in self.scanner_errors_by_line:
                for text in self.scanner_errors_by_line[line]:
                    self.errors.append((line, f'Invalid identifier "{text}"'))
                del self.scanner_errors_by_line[line]
                # Continue to next token after reporting error
                
            # Comment handling
            if token[2] in ['Comment Start', 'Comment Content', 'Comment End']:
                if token[2] == 'Comment Start':
                    self.matched_rules.append((line, 'comment'))
                # Consume all comment tokens
                while self.current < len(self.tokens) and self.peek()[2] in ['Comment Start', 'Comment Content', 'Comment End']:
                    self.current += 1
                continue
                
            # Function declaration
            if token[2] == 'Void':
                if self.try_function_declaration():
                    self.matched_rules.append((line, 'fun-declaration'))
                continue
                
            # Variable declaration
            if token[2] == 'Type':
                if self.try_variable_declaration():
                    self.matched_rules.append((line, 'var-declaration'))
                else:
                    # Skip to next token after type
                    self.current += 1
                continue
                
            # Loop statement
            if token[2] == 'Loop':
                if self.try_repeat_when():
                    self.matched_rules.append((line, 'iteration-stmt'))
                continue
                
            # Assignment statement
            if token[2] == 'Identifier':
                if self.try_assignment():
                    self.matched_rules.append((line, 'expression-stmt'))
                else:
                    self.current += 1
                continue
                
            # Closing braces and other tokens
            if token[2] == 'Braces' or token[2] == 'Semicolon':
                self.current += 1
                continue
                
            # If we reach here, no rule matched
            self.errors.append((line, f"Unexpected token: {token[1]}"))
            self.current += 1

    def try_function_declaration(self):
        """Try to match a function declaration"""
        # Save current position
        start_pos = self.current
        
        # Match return type (Void)
        if not self.consume_if_match(lambda t: t[2] == 'Void'):
            return False
            
        # Match function name (identifier)
        if not self.consume_if_match(lambda t: t[2] == 'Identifier'):
            self.current = start_pos
            return False
            
        # Match opening parenthesis
        if not self.consume_if_match(lambda t: t[1] == '(' and t[2] == 'Braces'):
            self.current = start_pos
            return False
            
        # Match closing parenthesis
        if not self.consume_if_match(lambda t: t[1] == ')' and t[2] == 'Braces'):
            self.current = start_pos
            return False
            
        # Match opening brace for function body
        if not self.consume_if_match(lambda t: t[1] == '{' and t[2] == 'Braces'):
            self.current = start_pos
            return False
            
        return True

    def try_variable_declaration(self):
        """Try to match a variable declaration"""
        # Save current position
        start_pos = self.current
        
        # Match type
        if not self.consume_if_match(lambda t: t[2] == 'Type'):
            return False
            
        # Check for scanner error on this line
        next_token = self.peek()
        if next_token:
            line = next_token[0]
            if line in self.scanner_errors_by_line:
                # We've found an invalid identifier - report it and continue parsing
                return False
            
        # Match identifier (if no scanner error)
        if not self.consume_if_match(lambda t: t[2] == 'Identifier'):
            self.current = start_pos
            return False
            
        # Match optional initialization
        if self.peek() and self.peek()[2] == 'Assignment operator':
            self.current += 1  # Consume '='
            
            # Consume expression
            if not self.consume_if_match(lambda t: t[2] == 'Constant' or t[2] == 'Identifier'):
                self.current = start_pos
                return False
            
        # Match semicolon
        if not self.consume_if_match(lambda t: t[2] == 'Semicolon'):
            self.current = start_pos
            return False
            
        return True

    def try_repeat_when(self):
        """Try to match a RepeatWhen loop"""
        # Save current position
        start_pos = self.current
        
        # Match RepeatWhen
        if not self.consume_if_match(lambda t: t[2] == 'Loop'):
            return False
            
        # Match opening parenthesis
        if not self.consume_if_match(lambda t: t[1] == '(' and t[2] == 'Braces'):
            self.current = start_pos
            return False
            
        # Consume condition tokens (first identifier)
        if not self.consume_if_match(lambda t: t[2] == 'Identifier'):
            self.current = start_pos
            return False
            
        # Consume comparison operator
        if not self.consume_if_match(lambda t: t[2] == 'Less Than' or t[2] == 'Greater Than' 
                                  or t[2] == 'Equal' or t[2] == 'Not Equal'):
            self.current = start_pos
            return False
            
        # Consume second part of condition
        if not self.consume_if_match(lambda t: t[2] == 'Identifier' or t[2] == 'Constant'):
            self.current = start_pos
            return False
            
        # Match closing parenthesis
        if not self.consume_if_match(lambda t: t[1] == ')' and t[2] == 'Braces'):
            self.current = start_pos
            return False
            
        # Match opening brace for loop body
        if not self.consume_if_match(lambda t: t[1] == '{' and t[2] == 'Braces'):
            self.current = start_pos
            return False
            
        return True

    def try_assignment(self):
        """Try to match an assignment statement"""
        # Save current position
        start_pos = self.current
        
        # Match identifier
        if not self.consume_if_match(lambda t: t[2] == 'Identifier'):
            return False
            
        # Match equals sign
        if not self.consume_if_match(lambda t: t[2] == 'Assignment operator'):
            self.current = start_pos
            return False
            
        # Match right-hand side (identifier)
        if not self.consume_if_match(lambda t: t[2] == 'Identifier'):
            self.current = start_pos
            return False
            
        # Match operator (optional)
        if self.peek() and self.peek()[2] in ['Plus', 'Minus', 'Multiply', 'Divide']:
            self.current += 1  # Consume operator
            
            # Match constant or identifier
            if not self.consume_if_match(lambda t: t[2] == 'Constant' or t[2] == 'Identifier'):
                self.current = start_pos
                return False
            
        # Match semicolon
        if not self.consume_if_match(lambda t: t[2] == 'Semicolon'):
            self.current = start_pos
            return False
            
        return True

    def consume_if_match(self, predicate):
        """Consume the current token if it matches the predicate"""
        token = self.peek()
        if token and predicate(token):
            self.current += 1
            return True
        return False

    def peek(self):
        """Get the current token without consuming it"""
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return None

    def print_results(self):
        """Print the parsing results"""
        print("\nParser Phase Output:")
        print("Firstly you must state Scanner phase output as in scanner sample input and output")
        print("then state Parser Phase output based on scanner output\n")
        # Sort matched rules by line number for cleaner output
        sorted_matches = sorted(self.matched_rules, key=lambda x: x[0])
        for line, rule in sorted_matches:
            print(f"Line : {line} Matched Rule used: {rule}")
        sorted_errors = sorted(self.errors, key=lambda x: x[0])
        for line, err in sorted_errors:
            print(f"Line : {line} Not Matched Error: {err}")
        print(f"\nTotal NO of errors: {len(self.errors)}")