class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.kata = None

class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.daftar_kata = {}  # Untuk akses cepat
    
    def tambah(self, kode, kata):
        """Menambahkan kode dan kata ke Trie"""
        node = self.root
        for char in kode:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end_of_word = True
        node.kata = kata
        self.daftar_kata[kode] = kata
    
    def cari(self, kode):
        """Mencari kata berdasarkan kode lengkap"""
        node = self.root
        for char in kode:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node.kata if node.is_end_of_word else None
    
    def cari_prefix(self, prefix):
        """Mencari semua kata dengan prefix tertentu"""
        node = self.root
        result = {}
        
        # Navigasi ke node prefix
        for char in prefix:
            if char not in node.children:
                return result
            node = node.children[char]
        
        # Kumpulkan semua kata dari node ini
        self._collect_words(node, prefix, result)
        return result
    
    def _collect_words(self, node, current_prefix, result):
        """Helper untuk mengumpulkan semua kata dari node"""
        if node.is_end_of_word:
            result[current_prefix] = node.kata
        
        for char, child_node in node.children.items():
            self._collect_words(child_node, current_prefix + char, result)
    
    def cari_terpanjang(self, rangkaian):
        """Mencari terjemahan terpanjang yang cocok"""
        node = self.root
        last_found = None
        current_prefix = ""
        
        for char in rangkaian:
            if char not in node.children:
                break
            
            node = node.children[char]
            current_prefix += char
            
            if node.is_end_of_word:
                last_found = node.kata
        
        return last_found