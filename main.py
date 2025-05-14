from scanner import Scanner
from pars import Parser

def main():
    filename = input("Enter input file name: ").strip()
    if not filename:
        print("No filename entered.")
        return

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()

        scanner = Scanner()
        tokens, errors = scanner.tokenize(code)
        scanner.print_tokens(tokens, errors)

        if not tokens:
            print("No tokens produced by scanner. Parser will not run.")
            return

        parser = Parser(tokens, errors)
        parser.parse()
        parser.print_results()

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()