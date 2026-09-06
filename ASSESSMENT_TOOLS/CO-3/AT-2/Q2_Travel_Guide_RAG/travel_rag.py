# ==============================================================
# TRAVEL GUIDE RAG ASSISTANT
# PDF + Embeddings + FAISS + Gemini
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

def extract_text(pdf_path):

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
# 2. Split document into chunks
# --------------------------------------------------------------

def split_into_chunks(text, chunk_size=800, overlap=100):

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
# 3. Generate embeddings
# --------------------------------------------------------------

def create_embeddings(chunks, model):

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings.astype("float32")


# --------------------------------------------------------------
# 4. Create FAISS database
# --------------------------------------------------------------

def create_faiss_database(embeddings):

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index


# --------------------------------------------------------------
# 5. Retrieve relevant travel information
# --------------------------------------------------------------

def retrieve_information(question, model, index, chunks, top_k=3):

    question_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    question_embedding = question_embedding.astype("float32")

    scores, indices = index.search(
        question_embedding,
        top_k
    )

    results = []

    for score, index_number in zip(scores[0], indices[0]):

        if index_number != -1:

            results.append({
                "text": chunks[index_number],
                "score": float(score)
            })

    return results


# --------------------------------------------------------------
# 6. Generate answer using Gemini
# --------------------------------------------------------------

def generate_answer(question, retrieved_data, client):

    context = "\n\n".join(
        item["text"]
        for item in retrieved_data
    )

    prompt = f"""
You are a helpful Travel Guide RAG Assistant.

Answer the user's question using ONLY the information
provided in the retrieved travel guide context.

Do not invent information.

If the answer is not available in the context,
respond:

"The requested information is not available
in the provided travel guide."

Give a clear and useful answer.

RETRIEVED TRAVEL GUIDE CONTEXT:
--------------------------------
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
    print("             TRAVEL GUIDE RAG ASSISTANT")
    print("=" * 70)

    # ----------------------------------------------------------
    # Check API key
    # ----------------------------------------------------------

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        print("\nERROR: Gemini API key not detected.")

        print('Set it using:')
        print('$env:GEMINI_API_KEY="YOUR_API_KEY"')

        return

    client = genai.Client(api_key=api_key)

    # ----------------------------------------------------------
    # Get PDF
    # ----------------------------------------------------------

    pdf_path = input("\nEnter travel guide PDF path: ").strip()

    if not pdf_path:

        print("\nERROR: PDF path cannot be empty.")

        return

    if not os.path.isfile(pdf_path):

        print("\nERROR: PDF file not found.")

        return

    # ----------------------------------------------------------
    # Extract text
    # ----------------------------------------------------------

    print("\n[1] Extracting travel guide text...")

    text = extract_text(pdf_path)

    if not text:

        print("\nERROR: No readable text found.")

        return

    print("Text extraction successful.")

    print("Characters extracted:", len(text))

    # ----------------------------------------------------------
    # Chunking
    # ----------------------------------------------------------

    print("\n[2] Splitting travel guide into chunks...")

    chunks = split_into_chunks(text)

    if not chunks:

        print("\nERROR: No chunks were created.")

        return

    print("Number of chunks:", len(chunks))

    # ----------------------------------------------------------
    # Embedding model
    # ----------------------------------------------------------

    print("\n[3] Loading embedding model...")

    try:

        model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("Embedding model loaded successfully.")

    except Exception as e:

        print("\nERROR loading embedding model:")

        print(e)

        return

    # ----------------------------------------------------------
    # Embeddings
    # ----------------------------------------------------------

    print("\n[4] Generating embeddings...")

    try:

        embeddings = create_embeddings(
            chunks,
            model
        )

        print("Embeddings generated successfully.")

        print(
            "Embedding dimension:",
            embeddings.shape[1]
        )

    except Exception as e:

        print("\nERROR generating embeddings:")

        print(e)

        return

    # ----------------------------------------------------------
    # FAISS
    # ----------------------------------------------------------

    print("\n[5] Creating FAISS vector database...")

    try:

        index = create_faiss_database(
            embeddings
        )

        print("FAISS database created successfully.")

        print(
            "Vectors stored:",
            index.ntotal
        )

    except Exception as e:

        print("\nERROR creating FAISS database:")

        print(e)

        return

    # ----------------------------------------------------------
    # Ready
    # ----------------------------------------------------------

    print("\n" + "=" * 70)

    print("              TRAVEL RAG SYSTEM READY")

    print("=" * 70)

    print("\nAsk questions about the travel guide.")

    print("Type 'exit' to stop.")

    # ----------------------------------------------------------
    # Question loop
    # ----------------------------------------------------------

    while True:

        question = input(
            "\nEnter your travel question: "
        ).strip()

        # Exit
        if question.lower() == "exit":

            print("\nTravel RAG Assistant stopped.")

            break

        # Empty input
        if not question:

            print(
                "ERROR: Question cannot be empty."
            )

            continue

        # ------------------------------------------------------
        # Retrieval
        # ------------------------------------------------------

        print(
            "\n[6] Searching travel guide..."
        )

        retrieved_data = retrieve_information(
            question,
            model,
            index,
            chunks,
            top_k=3
        )

        if not retrieved_data:

            print(
                "No relevant information found."
            )

            continue

        # ------------------------------------------------------
        # Display retrieved context
        # ------------------------------------------------------

        print("\n" + "=" * 70)

        print("             RETRIEVED TRAVEL CONTEXT")

        print("=" * 70)

        for i, item in enumerate(
            retrieved_data,
            start=1
        ):

            print(f"\nChunk {i}")

            print(
                f"Similarity Score: "
                f"{item['score']:.4f}"
            )

            print("-" * 70)

            print(item["text"][:1000])

        # ------------------------------------------------------
        # Relevance check
        # ------------------------------------------------------

        best_score = retrieved_data[0]["score"]

        if best_score < 0.25:

            print(
                "\nThis question does not appear "
                "to be related to the travel guide."
            )

            continue

        # ------------------------------------------------------
        # Generate response
        # ------------------------------------------------------

        print(
            "\n[7] Generating travel answer using Gemini..."
        )

        answer = generate_answer(
            question,
            retrieved_data,
            client
        )

        print("\n" + "=" * 70)

        print("                 TRAVEL ANSWER")

        print("=" * 70)

        print(answer)

        print("=" * 70)


# --------------------------------------------------------------
# Start program
# --------------------------------------------------------------

if __name__ == "__main__":

    main()