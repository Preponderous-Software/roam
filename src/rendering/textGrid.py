# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# A plain character grid backing the text frontend (frontend-abstraction epic
# #433 / #239). It is a backend-neutral, dependency-free buffer: the TextRenderer
# maps the game's pixel-space draw calls onto cells here, then renders the grid
# to a string for the terminal (or for assertions in tests). All writes are
# bounds-clipped, so off-screen draws are silently ignored rather than raising.
class TextGrid:
    def __init__(self, columns, rows, blank=" "):
        self.columns = columns
        self.rows = rows
        self._blank = blank
        self.clear()

    def clear(self):
        self._cells = [[self._blank] * self.columns for _ in range(self.rows)]

    def _inBounds(self, column, row):
        return 0 <= column < self.columns and 0 <= row < self.rows

    def setChar(self, column, row, char):
        if self._inBounds(column, row):
            self._cells[row][column] = char

    def getChar(self, column, row):
        if self._inBounds(column, row):
            return self._cells[row][column]
        return None

    def writeText(self, column, row, text):
        """Write text left-to-right starting at (column, row); clipped at the
        right edge and ignored if the row is out of range."""
        for offset, char in enumerate(text):
            self.setChar(column + offset, row, char)

    def fillRect(self, column, row, width, height, char):
        for r in range(row, row + height):
            for c in range(column, column + width):
                self.setChar(c, r, char)

    def drawBox(self, column, row, width, height):
        """Draw a single-line border outline of the given cell rectangle."""
        if width < 1 or height < 1:
            return
        right = column + width - 1
        bottom = row + height - 1
        self.setChar(column, row, "+")
        self.setChar(right, row, "+")
        self.setChar(column, bottom, "+")
        self.setChar(right, bottom, "+")
        for c in range(column + 1, right):
            self.setChar(c, row, "-")
            self.setChar(c, bottom, "-")
        for r in range(row + 1, bottom):
            self.setChar(column, r, "|")
            self.setChar(right, r, "|")

    def toString(self):
        return "\n".join("".join(row).rstrip() for row in self._cells)
