import os
import numpy as np
import pandas as pd
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

# Set up OpenAI API key
client = OpenAI()

# Load embeddings data from CSV
embeddings_df = pd.read_csv("embeddings.csv")

def generate_query_embedding(query, model="text-embedding-3-small"):
    """Generate an embedding for a search query."""
    try:
        response = client.embeddings.create(
            input=[query],
            model=model
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return None

def search(query, top_n=3):
    """Find the top N most similar text chunks to the query."""
    query_embedding = generate_query_embedding(query)
    if query_embedding is None:
        print("Query embedding generation failed.")
        return pd.DataFrame()  # Return an empty DataFrame if embedding generation fails
    
    # Convert embeddings in the CSV to numpy arrays
    embeddings = embeddings_df['embedding'].apply(eval).apply(np.array).tolist()
    
    # Calculate cosine similarity between query embedding and each chunk's embedding
    similarities = cosine_similarity([query_embedding], embeddings)[0]

    # Add similarities to the DataFrame and sort by similarity
    embeddings_df['similarity'] = similarities
    top_results = embeddings_df.sort_values(by='similarity', ascending=False).head(top_n)

    # Return the top matching results
    return top_results[['filename', 'text', 'similarity']]

def generate_answer(query, context_chunks):
    """Generate an answer to the query based on the retrieved context."""
    try:
        context = "\n\n".join(context_chunks)
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Answer the question based on the provided context. If unsure, say 'I don't know.'"},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
            ]
        )
        return response.choices[0].message.content  # Corrected access
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "I'm sorry, I couldn't generate an answer."

def ongoing_conversation():
    print("Chat with GPT-4o. Type 'exit' to end the conversation.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        # Retrieve the top 3 most relevant context chunks for the query
        results = search(user_input, top_n=3)
        if results.empty:  # Check if results DataFrame is empty
            print("No relevant information found.")
            continue

        # Get text chunks from the search results for answer generation
        context_chunks = results['text'].tolist()
        # Generate an answer based on the context and user query
        answer = generate_answer(user_input, context_chunks)
        print(f"GPT-4o: {answer}")

if __name__ == "__main__":
    ongoing_conversation()
