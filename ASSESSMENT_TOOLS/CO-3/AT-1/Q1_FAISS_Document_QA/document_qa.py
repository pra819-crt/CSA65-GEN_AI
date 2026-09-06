# ==============================================================
# FAISS-BASED DOCUMENT QUESTION ANSWERING SYSTEM
# Using Embeddings + FAISS + Gemini
# ==============================================================

import os
import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from google import genai


# --------------------------------------------------------------
# 1. Extract text from PDF
# --------------------------------------------------------------

def extract_text_from_pdf(pdf_path):
    """Extract text from all pages of a PDF."""

    try:
        reader = PdfReader(pdf_path)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text.strip()

    except Exception as e:
        print("\nERROR while reading PDF:")
        print(e)
        return ""


# --------------------------------------------------------------
# 2. Split text into chunks
# --------------------------------------------------------------

def split_text(text, chunk_size=800, overlap=100):
    """Split document text into overlapping chunks."""

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


# --------------------------------------------------------------
# 3. Create embeddings
# --------------------------------------------------------------

def create_embeddings(chunks, model):
    """Convert document chunks into embedding vectors."""

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings.astype("float32")


# --------------------------------------------------------------
# 4. Create FAISS index
# --------------------------------------------------------------

def create_faiss_index(embeddings):
    """Create a FAISS similarity-search index."""

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index


# --------------------------------------------------------------
# 5. Retrieve relevant chunks
# --------------------------------------------------------------

def retrieve_chunks(question, model, index, chunks, top_k=3):
    """Retrieve the most relevant document chunks."""

    question_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    question_embedding = question_embedding.astype("float32")

    scores, indices = index.search(question_embedding, top_k)

    results = []

    for score, index_number in zip(scores[0], indices[0]):

        if index_number != -1:

            results.append({
                "chunk": chunks[index_number],
                "score": float(score)
            })

    return results


# --------------------------------------------------------------
# 6. Generate answer using Gemini
# --------------------------------------------------------------

def generate_answer(question, retrieved_chunks, client):
    """Generate an answer using Gemini and retrieved context."""

    context = "\n\n".join(
        result["chunk"]
        for result in retrieved_chunks
    )

    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the information
provided in the document context below.

If the answer is not available in the context,
say clearly:

"The information is not available in the provided document."

Do not invent or assume information.

DOCUMENT CONTEXT:
-----------------
{context}

USER QUESTION:
--------------
{question}

ANSWER:
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        return f"ERROR while generating answer: {e}"


# --------------------------------------------------------------
# 7. Main program
# --------------------------------------------------------------

def main():

    print("=" * 70)
    print("              FAISS-BASED DOCUMENT QA")
    print("=" * 70)

    # ----------------------------------------------------------
    # Check Gemini API key
    # ----------------------------------------------------------

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        print("\nERROR: Gemini API key not detected.")

        print("Set it using:")
        print('$env:GEMINI_API_KEY="YOUR_API_KEY"')

        return

    # Create Gemini client
    client = genai.Client(api_key=api_key)

    # ----------------------------------------------------------
    # Get PDF path
    # ----------------------------------------------------------

    pdf_path = input("\nEnter PDF file path: ").strip()

    if not pdf_path:

        print("\nERROR: PDF path cannot be empty.")

        return

    if not os.path.isfile(pdf_path):

        print("\nERROR: PDF file not found.")
        print("Please check the file path.")

        return

    # ----------------------------------------------------------
    # Extract text
    # ----------------------------------------------------------

    print("\n[1] Extracting text from PDF...")

    text = extract_text_from_pdf(pdf_path)

    if not text:

        print("\nERROR: No readable text found in the PDF.")

        return

    print("Text extraction successful.")
    print("Characters extracted:", len(text))

    # ----------------------------------------------------------
    # Chunking
    # ----------------------------------------------------------

    print("\n[2] Splitting document into chunks...")

    chunks = split_text(text)

    if not chunks:

        print("\nERROR: Could not create document chunks.")

        return

    print("Number of chunks:", len(chunks))

    # ----------------------------------------------------------
    # Load embedding model
    # ----------------------------------------------------------

    print("\n[3] Loading embedding model...")

    try:

        model = SentenceTransformer("all-MiniLM-L6-v2")

        print("Embedding model loaded successfully.")

    except Exception as e:

        print("\nERROR while loading embedding model:")
        print(e)

        return

    # ----------------------------------------------------------
    # Generate embeddings
    # ----------------------------------------------------------

    print("\n[4] Generating embeddings...")

    try:

        embeddings = create_embeddings(chunks, model)

        print("Embeddings generated successfully.")
        print("Embedding dimension:", embeddings.shape[1])

    except Exception as e:

        print("\nERROR while generating embeddings:")
        print(e)

        return

    # ----------------------------------------------------------
    # Create FAISS database
    # ----------------------------------------------------------

    print("\n[5] Creating FAISS vector database...")

    try:

        index = create_faiss_index(embeddings)

        print("FAISS index created successfully.")
        print("Vectors stored:", index.ntotal)

    except Exception as e:

        print("\nERROR while creating FAISS index:")
        print(e)

        return

    # ----------------------------------------------------------
    # Question-answering loop
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("                 DOCUMENT QA READY")
    print("=" * 70)

    print("\nYou can ask questions about the document.")
    print("Type 'exit' to stop the program.")

    while True:

        question = input("\nEnter your question: ").strip()

        # Exit condition
        if question.lower() == "exit":
            print("\nProgram terminated.")
            break

        # Empty question handling
        if not question:

            print("ERROR: Question cannot be empty.")
            continue

        # ------------------------------------------------------
        # Retrieval
        # ------------------------------------------------------

        print("\n[6] Performing semantic search...")

        retrieved_chunks = retrieve_chunks(
            question,
            model,
            index,
            chunks,
            top_k=3
        )

        if not retrieved_chunks:

            print("No relevant information found.")

            continue

        # ------------------------------------------------------
        # Display retrieved context
        # ------------------------------------------------------

        print("\n" + "=" * 70)
        print("                 RETRIEVED CONTEXT")
        print("=" * 70)

        for i, result in enumerate(retrieved_chunks, start=1):

            print(f"\nChunk {i}")
            print(f"Similarity Score: {result['score']:.4f}")
            print("-" * 70)
            print(result["chunk"][:1000])

        # ------------------------------------------------------
        # Relevance check
        # ------------------------------------------------------

        best_score = retrieved_chunks[0]["score"]

        if best_score < 0.25:

            print("\nThe question does not appear to be related")
            print("to the provided document.")

            continue

        # ------------------------------------------------------
        # Generate answer
        # ------------------------------------------------------

        print("\n[7] Generating answer using Gemini...")

        answer = generate_answer(
            question,
            retrieved_chunks,
            client
        )

        print("\n" + "=" * 70)
        print("                    GENERATED ANSWER")
        print("=" * 70)

        print(answer)

        print("=" * 70)


# --------------------------------------------------------------
# Run program
# --------------------------------------------------------------

if __name__ == "__main__":
    main()