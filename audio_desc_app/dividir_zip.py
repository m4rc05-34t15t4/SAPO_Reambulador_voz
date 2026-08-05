import os
import zipfile
import sys

def zip_and_split():
    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(plugin_dir, "sapo_audio_desc_point")
    zip_filename = os.path.join(plugin_dir, "SAPO_Audio_Point_v1.1.0.zip")

    if not os.path.exists(target_dir):
        print(f"Erro: pasta {target_dir} nao existe.")
        return

    print(f"1. Compactando pasta '{target_dir}' para '{zip_filename}'...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, plugin_dir)
                zf.write(full_path, rel_path)

    total_size = os.path.getsize(zip_filename)
    print(f"   ZIP criado com sucesso! Tamanho total: {total_size / (1024*1024):.2f} MB")

    # Divisão em partes de 90 MB (94.371.840 bytes) para ter margem bem segura no limit do GitHub (100MB)
    chunk_size = 90 * 1024 * 1024
    part_num = 1

    print("\n2. Dividindo arquivo ZIP em partes menores que 90 MB...")
    with open(zip_filename, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            part_name = f"{zip_filename}.{part_num:03d}"
            with open(part_name, 'wb') as pf:
                pf.write(chunk)
            print(f"   Criado: {os.path.basename(part_name)} ({len(chunk) / (1024*1024):.2f} MB)")
            part_num += 1

    os.remove(zip_filename)
    print("\n✅ Processo concluido! Arquivo original ZIP removido, partes geradas prontas.")

if __name__ == "__main__":
    zip_and_split()
