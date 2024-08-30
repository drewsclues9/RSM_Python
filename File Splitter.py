import pandas as pd

def split_large_file(input_file, output_prefix, max_rows=25000):
    # Read the entire file as objects to prevent any data conversion
    df = pd.read_csv(input_file, dtype=object)
    
    # Group by TransactionID
    grouped = df.groupby('BatNbr', sort=False)
    
    current_chunk = []
    current_chunk_size = 0
    file_index = 1
    
    for name, group in grouped:
        group_size = len(group)
        
        # Check if adding this group would exceed the max_rows limit
        if current_chunk_size + group_size > max_rows:
            # Write the current chunk to a file
            output_file = f"{output_prefix}_part{file_index}.csv"
            pd.concat(current_chunk).to_csv(output_file, index=False, encoding='utf-8')
            
            # Reset for the next chunk
            current_chunk = []
            current_chunk_size = 0
            file_index += 1
        
        # Add the group to the current chunk
        current_chunk.append(group)
        current_chunk_size += group_size
    
    # Write the last chunk if it has any data
    if current_chunk:
        output_file = f"{output_prefix}_part{file_index}.csv"
        pd.concat(current_chunk).to_csv(output_file, index=False, encoding='utf-8')

# Example usage:
input_file = 'C:/Users/E075882/OneDrive - RSM/All Data/Client/SHO-ME/Data Uploads/Inventory Journals Upload.csv'
output_prefix = 'C:/Users/E075882/OneDrive - RSM/All Data/Client/cache/test'
split_large_file(input_file, output_prefix)