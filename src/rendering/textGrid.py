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
        self._clip = None  # (col0, row0, col1, row1) exclusive, or None
        self.clear()

    def setClipRegion(self, col0, row0, col1, row1):
        """Restrict all subsequent writes to cells in [col0,col1) × [row0,row1).
        Pass None for col0 to clear the clip region."""
        self._clip = None if col0 is None else (col0, row0, col1, row1)

    def clear(self):
        self._cells = [[self._blank] * self.columns for _ in range(self.rows)]
        self._colors = [[None] * self.columns for _ in range(self.rows)]

    def _inBounds(self, column, row):
        if not (0 <= column < self.columns and 0 <= row < self.rows):
            return False
        if self._clip is not None:
            col0, row0, col1, row1 = self._clip
            return col0 <= column < col1 and row0 <= row < row1
        return True

    def setChar(self, column, row, char):
        if self._inBounds(column, row):
            self._cells[row][column] = char

    def setColor(self, column, row, ansiCode):
        """Attach an ANSI foreground color code to a cell (e.g. 32 for green).
        Pass None to clear. Only applied when toString() builds the frame."""
        if self._inBounds(column, row):
            self._colors[row][column] = ansiCode

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
        lines = []
        for rowIdx, row in enumerate(self._cells):
            colorRow = self._colors[rowIdx]
            # Determine last non-space column so we can rstrip correctly even
            # when ANSI codes are present (they would foil a plain str.rstrip).
            last = -1
            for c in range(self.columns - 1, -1, -1):
                if row[c] != " ":
                    last = c
                    break
            parts = []
            for c in range(last + 1):
                char = row[c]
                code = colorRow[c]
                if code is not None and char != " ":
                    parts.append(f"\033[{code}m{char}\033[0m")
                else:
                    parts.append(char)
            lines.append("".join(parts))
        return "\n".join(lines)
