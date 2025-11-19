# Medit
<sub>psst... check out [tedit by Robertflexx](https://github.com/Robertflexx/tedit)</sub>
> Micro Edit

A hyper minimal text editor for your terminal built with Python
## Features
- Extremely lightweight and fast
- No curses or ncurses, pure terminal I/O
- Basic text editing capabilities
- Simple and intuitive interface
## Installation
You can install Medit using pip:
```bash
pip install MicroEdit
```
## Usage
```bash
medit <filename>
```
## Controls
- `h | help`: help
- `q | quit`: quit medit
- `s | save`: save file
- `u | up [AMOUNT]`: move cursor up AMOUNT lines (optional)
- `d | down [AMOUNT]`: move cursor down AMOUNT lines (optional)
- `a | add [TEXT]`: adds a newline with TEXT below the current line (optional)
- `r | remove`: removes the current line
- `e | edit [TEXT]`: replaces the current line with TEXT (optional)
- `i | insert [TEXT]`: inserts TEXT after the current line's content (optional)

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue.
## License
This project is licensed under the [Zlib License](LICENSE).
