class Parser:
    def __init__(self, tokens, scanner_errors):
        self.tokens = tokens
        self.scanner_errors = scanner_errors
        self.current_token_idx = 0
        self.current_line = 1
        self.errors = []
        self.matched_rules = []
        
    def parse(self):
        self.program()
        return self.matched_rules, self.errors
    
    def match(self, expected_type):
        token = self.peek()
        if token and token[2] == expected_type:
            self.current_token_idx += 1
            self.current_line = token[0]
            return True
        return False

    def peek(self):
        if self.current_token_idx < len(self.tokens):
            return self.tokens[self.current_token_idx]
        return None

    def add_matched_rule(self, rule):
        self.matched_rules.append((self.current_line, rule))
    
    def add_error(self, message):
        self.errors.append((self.current_line, message))

    def program(self):
        while self.current_token_idx < len(self.tokens):
            token = self.peek()
            if not token:
                break
                
            # Check for comments
            if token[2] == 'Comment Start':
                self.add_matched_rule("Matched Rule used: Comment")
                # Skip past all comment tokens
                while self.current_token_idx < len(self.tokens) and \
                      self.tokens[self.current_token_idx][2] in {'Comment Start', 'Comment Content', 'Comment End'}:
                    self.current_token_idx += 1
                continue
            
            # Check for invalid identifiers from scanner errors
            is_invalid = False
            for error in self.scanner_errors:
                if token and token[0] == error[0]:  # Same line number
                    self.add_error(f'Invalid identifier "{error[1]}"')
                    is_invalid = True
                    break
                    
            if is_invalid:
                # Skip past this token
                self.current_token_idx += 1
                continue
                
            # Try declarations
            orig_idx = self.current_token_idx
            if self.fun_declaration():
                continue
                
            # Skip token if nothing matched
            self.current_token_idx += 1

    def fun_declaration(self):
        orig_idx = self.current_token_idx
        if self.match('Void') and self.match('Identifier') and \
           self.match('Braces') and self.match('Braces') and \
           self.compound_stmt():
            self.add_matched_rule("Matched Rule used: fun-declaration")
            return True
        self.current_token_idx = orig_idx
        return False

    def compound_stmt(self):
        if self.match('Braces'):  # Opening {
            # Skip everything until closing }
            brace_depth = 1
            while self.current_token_idx < len(self.tokens):
                token = self.peek()
                if not token:
                    break
                    
                if token[1] == '{':
                    brace_depth += 1
                elif token[1] == '}':
                    brace_depth -= 1
                    if brace_depth == 0:
                        self.match('Braces')  # Match closing }
                        return True
                        
                self.current_token_idx += 1
        return False

    def print_results(self):
        print("Parser Phase Output:")
        for rule in self.matched_rules:
            print(f"Line : {rule[0]} {rule[1]}")
            
        for error in self.errors:
            print(f"Line : {error[0]} Not Matched Error: {error[1]}")
            
        print(f"Total NO of errors: {len(self.errors)}")