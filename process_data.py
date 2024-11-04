# process_data.py
import os
import pandas as pd
import tiktoken

def load_and_clean_text(directory="crawled_content"):
    """Load and clean text data from crawled .txt files."""
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' does not exist.")
    
    texts = []
    files = os.listdir(directory)
    
    if not files:
        raise FileNotFoundError(f"No files found in directory '{directory}'.")

    for filename in files:
        filepath = os.path.join(directory, filename)
        
        # Load the text content
        with open(filepath, "r", encoding="utf-8") as file:
            text = file.read()
        
        # Clean the text by removing extra whitespace and newlines
        text = " ".join(text.split())
        
        # Store the cleaned text with its filename
        texts.append((filename, text))
    
    # Convert to a DataFrame for easy handling
    df = pd.DataFrame(texts, columns=["filename", "text"])
    return df


def tokenize_and_chunk(df, max_tokens=500):
    """Split text data into chunks of a maximum number of tokens."""
    tokenizer = tiktoken.get_encoding("cl100k_base")
    
    chunks = []
    
    for _, row in df.iterrows():
        text = row["text"]
        tokens = tokenizer.encode(text)
        
        # Break down tokens into chunks
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append({"filename": row["filename"], "text": chunk_text})
    
    # Convert to a DataFrame for easy handling
    chunked_df = pd.DataFrame(chunks)
    return chunked_df

# Run the processing pipeline
df = load_and_clean_text()
chunked_df = tokenize_and_chunk(df)
print(chunked_df.head())

# Save to CSV for future reference
chunked_df.to_csv("processed_chunks.csv", index=False)
print("Chunked data saved to 'processed_chunks.csv'")