import hashlib

def calculate_md5(file_path):
    # Create an MD5 hash object
    md5_hash = hashlib.md5()
    
    # Open the file in binary mode
    with open(file_path, "rb") as f:
        # Read and update the hash in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    
    # Return the hexadecimal digest of the hash
    return md5_hash.hexdigest()