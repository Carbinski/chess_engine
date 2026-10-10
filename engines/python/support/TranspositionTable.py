class TranspositionTable:
    def __init__(self, num_entries=1000000):
        self.size = num_entries
        self.table = [None] * self.size

    def store(self, key, depth, score, flag, move):
        index = key % self.size

        entry = self.table[index]
        if entry is None or entry[1] <= depth:
            self.table[index] = (key, depth, score, flag, move)
    
    def probe(self, key):
        index = key % self.size
        entry = self.table[index]

        if entry is not None and entry[0] == key:
            return entry
        return None