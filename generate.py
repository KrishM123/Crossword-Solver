import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        for ele in self.domains:
            new = set()
            for words in self.domains[ele]:
                if len(words) == ele.length:
                    new.add(words)
            self.domains[ele] = new

    def revise(self, x, y):
        overlaps = self.crossword.overlaps
        temp = {}
        for ele in overlaps:
            if overlaps[ele] is not None:
                temp[ele] = overlaps[ele]
        overlaps = temp
        revised = False
        if overlaps[(x, y)] is not None:
            (x_pos, y_pos) = overlaps[(x, y)]
            new = set()
            for xword in self.domains[x]:
                works = False
                for yword in self.domains[y]:
                    if xword[x_pos] == yword[y_pos]:
                        works = True
                if works == True:
                    new.add(xword)
                else:
                    revised = True
            self.domains[x] = new
        return revised

    def ac3(self, arcs=None):
        if arcs is None:
            arcs = list()
            for x in self.domains:
                for y in self.crossword.neighbors(x):
                    arcs.append((x, y))

        while arcs is True:
            x, y = arcs.pop()

            if self.revise(x, y):
                if not self.domains[x]:
                    return False
                for new in self.crossword.neighbors(x) - self.domains[y]:
                    arcs.append((new, x))

        return True

    def assignment_complete(self, assignment):
        if len(assignment) == len(self.domains):
            return True

    def consistent(self, assignment):
        overlaps = self.crossword.overlaps
        temp = {}
        for ele in overlaps:
            if overlaps[ele] is not None:
                temp[ele] = overlaps[ele]
        overlaps = temp
        for (x, y) in overlaps:
            if x not in assignment or y not in assignment:
                continue
            (xpos, ypos) = overlaps[(x, y)]
            if assignment[x][xpos] != assignment[y][ypos]:
                return False
        return True

    def order_domain_values(self, var, assignment):
        nums = dict()

        for value in self.domains[var]:
            nums[value] = 0
            loopset = self.crossword.neighbors(var) - assignment
            for neighbour in loopset:
                if value in self.domains[neighbour]:
                    nums[value] += 1

        return sorted(nums, key=nums.get)

    def select_unassigned_variable(self, assignment):
        overlaps = self.crossword.overlaps
        temp = {}
        for ele in overlaps:
            if overlaps[ele] is not None:
                temp[ele] = overlaps[ele]
        overlaps = temp

        good = set()
        min = 999999999999
        for var in self.domains:
            if len(self.domains[var]) < min and var not in assignment:
                min = len(self.domains[var])

        for var in self.domains:
            if len(self.domains[var]) == min and var not in assignment:
                good.add(var)

        if len(good) == 1:
            return good.pop()
        count = {}
        for var in good:
            if var not in assignment:
                co = 0
                for ele in overlaps:
                    if var in ele:
                        co += 1
                count[var] = co
        lowest = set()
        min = 999999999999
        for ele in count:
            if count[ele] < min:
                min = count[ele]

        for ele in count:
            if count[ele] == min:
                lowest.add(ele)

        return lowest.pop()

    def backtrack(self, assignment):
        if self.assignment_complete(assignment):
            return assignment

        ele = self.select_unassigned_variable(assignment)

        for pos in self.domains[ele]:
            assignment[ele] = pos

            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result is not None:
                    return result

            assignment.pop(ele)

        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = f'data\{sys.argv[1]}'
    words = f'data\{sys.argv[2]}'
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
