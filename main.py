from scanner import Scanner
from pars import Parser

def main():
    # Get input file from user
    filename = input("Enter input file name: ")
    
    try:
        with open(filename, 'r') as f:
            code = f.read()
        
        scanner = Scanner()
        tokens, errors = scanner.tokenize(code)
        
        # Print scanner output
        scanner.print_tokens(tokens, errors)
        
        # Parse and print parser output
        parser = Parser(tokens, errors)
        parser.parse()
        parser.print_results()
        
        print("\nNote: The full implementation would include all grammar rules from the specification.")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
    
if __name__ == "__main__":
    main()