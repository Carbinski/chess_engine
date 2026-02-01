package org.Polygot;

import java.io.*;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class PolygotOpeningBook {

    private final List<BookEntry> library = new ArrayList<>();

    public PolygotOpeningBook() {
    }

    public PolygotOpeningBook(String bookPath) throws IOException {
        readData(new File(bookPath));
    }

    public void readData(File file) throws IOException {
        System.out.println("Loading Polygot Book: " + file.getAbsolutePath());
        library.clear();
        byte[] data = Files.readAllBytes(file.toPath());
        
        // Each entry is 16 bytes
        int entries = data.length / 16;
        for (int i = 0; i < entries; i++) {
            byte[] entryData = new byte[16];
            System.arraycopy(data, i * 16, entryData, 0, 16);
            library.add(new BookEntry(entryData));
        }
        
        // Ensure sorted for binary search
        Collections.sort(library);
        System.out.println("Loaded " + library.size() + " entries.");
    }

    public List<BookEntry> getEntries() {
        return library;
    }

    /**
     * Finds all book entries for a specific Zobrist Key using Binary Search.
     * Since there can be multiple moves for the same position, we find one match
     * and then scan neighbors to find all entries with the same key.
     */
    public List<BookEntry> findEntriesByKey(long key) {
        List<BookEntry> result = new ArrayList<>();
        if (library.isEmpty()) return result;

        // Dummy entry for search
        BookEntry searchKey = new BookEntry(key, 0, 0);

        int index = Collections.binarySearch(library, searchKey);

        if (index < 0) {
            return result; // Not found
        }

        // Found one match, now expand to find all matches with the same key
        // Scan backwards
        int i = index;
        while (i >= 0 && library.get(i).getKey() == key) {
            result.add(library.get(i));
            i--;
        }

        // Scan forwards (skip index itself since we just added it in backward scan if we started at index)
        // Wait, backward scan included 'index'. Let's be careful not to duplicate or miss.
        
        // Let's reset and clear result to be safe and simple.
        result.clear();
        
        // Go to the first occurrence
        i = index;
        while (i > 0 && library.get(i - 1).getKey() == key) {
            i--;
        }
        
        // Now iterate forward adding all matches
        while (i < library.size() && library.get(i).getKey() == key) {
            result.add(library.get(i));
            i++;
        }

        return result;
    }
}
