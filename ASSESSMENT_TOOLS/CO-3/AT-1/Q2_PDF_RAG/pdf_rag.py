# ---------------------------------------------------------
# PDF-Based RAG System
# Generative AI Assessment - Question 2
# ---------------------------------------------------------

import os
import numpy as np
import faiss

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from google import genai


# ---------------------------------------------------------
# Function 1: Extract Text from PDF
# ---------------------------------------------------------
def extract_text_from_pdf(pdf_path):
    """
    Reads the PDF and extracts text from all pages.
    """

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# ---------------------------------------------------------
# Function 2: Split Text into Chunks
# ---------------------------------------------------------
def split_into_chunks(text, chunk_size=500):
    """
    Splits the extracted text into smaller chunks.

    chunk_size represents the approximate number
    of characters in each chunk.
    """

    words = text.split()

    chunks = []

    current_chunk = ""

    for word in words:

        # Add the next word to the current chunk
        if len(current_chunk) + len(word) + 1 <= chunk_size:
            current_chunk += word + " "

        else:
            chunks.append(current_chunk.strip())
            current_chunk = word + " "

    # Add the remaining text
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


# ---------------------------------------------------------
# Function 3: Generate Embeddings
# ---------------------------------------------------------
def generate_embeddings(chunks):
    """
    Converts each text chunk into a numerical vector
    using a Sentence Transformer model.
    """

    print("\nLoading embedding model...")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Generating embeddings...")

    embeddings = model.encode(chunks)

    return model, np.array(embeddings).astype("float32")


# ---------------------------------------------------------
# Function 4: Create FAISS Vector Database
# ---------------------------------------------------------
def create_faiss_index(embeddings):
    """
    Creates a FAISS index and stores the embeddings.
    """

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    return index


# ---------------------------------------------------------
# Function 5: Retrieve Relevant Chunks
# ---------------------------------------------------------
def retrieve_chunks(query, model, index, chunks, top_k=3):
    """
    Converts the user query into an embedding and retrieves
    the most relevant document chunks using FAISS.
    """

    query_embedding = model.encode([query])

    query_embedding = np.array(query_embedding).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    retrieved_chunks = []

    for i in indices[0]:

        if i < len(chunks):
            retrieved_chunks.append(chunks[i])

    return retrieved_chunks, distances[0]


# ---------------------------------------------------------
# Function 6: Generate Answer Using Gemini
# ---------------------------------------------------------
def generate_answer(client, query, retrieved_chunks):
    """
    Sends the retrieved information and user question
    to Gemini to generate a grounded answer.
    """

    context = "\n\n".join(retrieved_chunks)

    prompt = f"""
You are a helpful question-answering assistant.

Answer the user's question using ONLY the information
provided in the retrieved document context.

If the answer cannot be found in the context,
say:

"The answer is not available in the provided document."

Retrieved Context:
{context}

User Question:
{query}

Give a clear and concise answer.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text


# ---------------------------------------------------------
# Main Program
# ---------------------------------------------------------
def main():

    print("=" * 70)
    print("             PDF-BASED RAG SYSTEM")
    print("=" * 70)

    # -----------------------------------------------------
    # Check Gemini API key
    # -----------------------------------------------------

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        print("\nERROR: Gemini API key not found.")

        print("Please set the GEMINI_API_KEY environment variable.")

        return

    # Create Gemini client
    client = genai.Client(api_key=api_key)

    # -----------------------------------------------------
    # Ask user for PDF path
    # -----------------------------------------------------

    pdf_path = input("\nEnter PDF file path: ").strip()

    if not pdf_path:

        print("\nERROR: PDF path cannot be empty.")

        return

    # Check whether PDF exists
    if not os.path.exists(pdf_path):

        print("\nERROR: PDF file not found.")

        print("Please check the file path.")

        return

    # -----------------------------------------------------
    # Step 1: Extract PDF text
    # -----------------------------------------------------

    print("\n[1] Extracting text from PDF...")

    try:

        text = extract_text_from_pdf(pdf_path)

    except Exception as error:

        print("\nERROR while reading PDF:")
        print(error)

        return

    if not text.strip():

        print("\nERROR: No readable text found in PDF.")

        return

    print("Text extraction successful.")

    print("Characters extracted:", len(text))

    # -----------------------------------------------------
    # Step 2: Split text into chunks
    # -----------------------------------------------------

    print("\n[2] Splitting text into chunks...")

    chunks = split_into_chunks(text)

    print("Number of chunks:", len(chunks))

    # Display chunks for demonstration
    print("\nSample chunks:")

    for i, chunk in enumerate(chunks[:3]):

        print(f"\nChunk {i + 1}:")
        print(chunk[:300])

    # -----------------------------------------------------
    # Step 3: Generate embeddings
    # -----------------------------------------------------

    try:

        model, embeddings = generate_embeddings(chunks)

    except Exception as error:

        print("\nERROR while generating embeddings:")
        print(error)

        return

    print("Embedding generation successful.")

    print("Embedding dimension:", embeddings.shape[1])

    # -----------------------------------------------------
    # Step 4: Store embeddings in FAISS
    # -----------------------------------------------------

    print("\n[4] Creating FAISS vector database...")

    try:

        index = create_faiss_index(embeddings)

    except Exception as error:

        print("\nERROR while creating FAISS index:")
        print(error)

        return

    print("FAISS index created successfully.")

    print("Vectors stored:", index.ntotal)

    # -----------------------------------------------------
    # Step 5: Get user question
    # -----------------------------------------------------

    query = input("\nEnter your question about the PDF: ").strip()

    if not query:

        print("\nERROR: Question cannot be empty.")

        return

    # -----------------------------------------------------
    # Step 6: Retrieve relevant chunks
    # -----------------------------------------------------

    print("\n[5] Retrieving relevant chunks...")

    try:

        retrieved_chunks, distances = retrieve_chunks(
            query,
            model,
            index,
            chunks,
            top_k=3
        )

    except Exception as error:

        print("\nERROR during retrieval:")
        print(error)

        return

    print("\nRETRIEVAL RESULTS")
    print("-" * 70)

    for i, chunk in enumerate(retrieved_chunks):

        print(f"\nRetrieved Chunk {i + 1}")
        print("Distance:", round(float(distances[i]), 4))
        print("Content:")
        print(chunk)

    # -----------------------------------------------------
    # Step 7: Generate answer using Gemini
    # -----------------------------------------------------

    print("\n[6] Generating answer using Gemini...")

    try:

        answer = generate_answer(
            client,
            query,
            retrieved_chunks
        )

    except Exception as error:

        print("\nERROR while calling Gemini API:")
        print(error)

        return

    # -----------------------------------------------------
    # Display final answer
    # -----------------------------------------------------

    print("\n" + "=" * 70)
    print("                    FINAL ANSWER")
    print("=" * 70)

    print(answer)

    print("=" * 70)


# ---------------------------------------------------------
# Program Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    main()