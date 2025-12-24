from trie import Trie
import os

class Penerjemah:
    def __init__(self, kamus_file="kamus.txt"):
        self.trie = Trie()
        self.kalimat_sementara = []
        self.kalimat_final = []
        self.load_kamus(kamus_file)
    
    def load_kamus(self, filename):
        """Memuat kamus dari file"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line and '=' in line:
                        kode, kata = line.split('=', 1)
                        self.trie.tambah(kode.strip(), kata.strip())
            print(f"Kamus berhasil dimuat: {len(self.trie.daftar_kata)} entri")
        except FileNotFoundError:
            print(f"File {filename} tidak ditemukan. Membuat kamus default.")
            self.create_default_kamus()
            self.save_kamus(filename)
    
    def create_default_kamus(self):
        """Membuat kamus default jika file tidak ditemukan"""
        default_kamus = {
            "1": "saya",
            "12": "kamu",
            "123": "dia",
            "2": "pergi",
            "23": "makan",
            "3": "ke",
            "34": "dari",
            "4": "sekolah",
            "45": "rumah",
            "5": "pada",
            "56": "dengan",
            "6": "hari",
            "67": "ini",
            "7": "."
        }
        
        for kode, kata in default_kamus.items():
            self.trie.tambah(kode, kata)
    
    def save_kamus(self, filename):
        """Menyimpan kamus ke file"""
        with open(filename, 'w', encoding='utf-8') as file:
            for kode, kata in self.trie.daftar_kata.items():
                file.write(f"{kode}={kata}\n")
    
    def proses_input(self, input_nada):
        """Memproses input nada"""
        if not input_nada:
            return
        
        # Tambahkan ke kalimat sementara
        self.kalimat_sementara.append(input_nada)
        
        # Coba terjemahkan rangkaian nada
        rangkaian = ''.join(self.kalimat_sementara)
        terjemahan = self.trie.cari_terpanjang(rangkaian)
        
        return terjemahan
    
    def get_kalimat_sementara(self):
        """Mendapatkan kalimat sementara untuk preview"""
        if not self.kalimat_sementara:
            return ""
        
        rangkaian = ''.join(self.kalimat_sementara)
        terjemahan = self.trie.cari_terpanjang(rangkaian)
        
        if terjemahan:
            return terjemahan
        else:
            # Tampilkan rangkaian kode jika belum ada terjemahan
            return ' '.join(self.kalimat_sementara)
    
    def get_kalimat(self):
        """Mendapatkan kalimat final"""
        if not self.kalimat_sementara:
            return ""
        
        # Coba terjemahkan semua
        rangkaian = ''.join(self.kalimat_sementara)
        hasil = []
        i = 0
        
        while i < len(rangkaian):
            terjemahan = self.trie.cari_prefix(rangkaian[i:])
            if terjemahan:
                # Gunakan terjemahan terpanjang yang ditemukan
                terpanjang = max(terjemahan.keys(), key=len)
                hasil.append(self.trie.daftar_kata[terpanjang])
                i += len(terpanjang)
            else:
                # Jika tidak ditemukan, gunakan kode asli
                hasil.append(rangkaian[i])
                i += 1
        
        self.kalimat_final.extend(hasil)
        return ' '.join(hasil)
    
    def reset(self):
        """Reset state penerjemah"""
        self.kalimat_sementara = []
    
    def tambah_kata(self, kode, kata):
        """Menambah kata baru ke kamus"""
        self.trie.tambah(kode, kata)