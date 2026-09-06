# Q1: FAISS Index Persistence
# Creates 2000 document embeddings,
# stores them in FAISS, performs semantic search,
# and saves the index to disk.

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# 1. Generate document dataset
# ---------------------------------------------------------

def create_documents():

    documents = []

    topics = [
        "Artificial Intelligence",
        "Machine Learning",
        "Deep Learning",
        "Generative AI",
        "Natural Language Processing",
        "Computer Vision",
        "Reinforcement Learning",
        "Data Science",
        "Robotics",
        "Cyber Security"
    ]

    for i in range(2000):

        topic = topics[i % len(topics)]

        text = (
            f"Document {i + 1}: "
            f"This document discusses {topic}. "
            f"It explains important concepts, applications, "
            f"methods, advantages and real-world uses of {topic}. "
            f"The document is part of a semantic search dataset."
        )

        documents.append(text)

    return documents


# ---------------------------------------------------------
# 2. Generate embeddings
# ---------------------------------------------------------

def generate_embeddings(documents):

    print("\n[1] Loading embedding model...")

    model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    print("Embedding model loaded successfully.")

    print("\n[2] Generating embeddings for 2000 documents...")

    embeddings = model.encode(
        documents,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    embeddings = embeddings.astype("float32")

    print("Embeddings generated successfully.")
    print("Number of embeddings:", len(embeddings))
    print("Embedding dimension:", embeddings.shape[1])

    return model, embeddings


# ---------------------------------------------------------
# 3. Create FAISS index
# ---------------------------------------------------------

def create_faiss_index(embeddings):

    print("\n[3] Creating FAISS index...")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(embeddings)

    print("FAISS index created successfully.")
    print("Vectors stored:", index.ntotal)

    return index


# ---------------------------------------------------------
# 4. Perform semantic search
# ---------------------------------------------------------

def semantic_search(
    model,
    index,
    documents,
    query
):

    print("\n[4] Performing semantic search...")
    print("Query:", query)

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    distances, indices = index.search(
        query_embedding,
        3
    )

    print("\nTop 3 Retrieved Documents:")

    results = []

    for rank, idx in enumerate(
        indices[0],
        start=1
    ):

        idx = int(idx)

        distance = float(
            distances[0][rank - 1]
        )

        print("\nRank", rank)
        print(
            "Document Index:",
            idx
        )
        print(
            "Distance:",
            round(distance, 4)
        )
        print(
            "Document:",
            documents[idx]
        )

        results.append(
            (idx, distance)
        )

    return results


# ---------------------------------------------------------
# 5. Main program
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print(
        "          FAISS INDEX PERSISTENCE - CREATE PROGRAM"
    )
    print("=" * 70)

    # -----------------------------------------------------
    # Create documents
    # -----------------------------------------------------

    documents = create_documents()

    print(
        "\nTotal documents created:",
        len(documents)
    )

    # -----------------------------------------------------
    # Generate embeddings
    # -----------------------------------------------------

    model, embeddings = generate_embeddings(
        documents
    )

    # -----------------------------------------------------
    # Create FAISS index
    # -----------------------------------------------------

    index = create_faiss_index(
        embeddings
    )

    # -----------------------------------------------------
    # Ask user for query
    # -----------------------------------------------------

    query = input(
        "\nEnter a search query: "
    ).strip()

    if not query:

        print(
            "ERROR: Query cannot be empty."
        )

        return

    # -----------------------------------------------------
    # Search before persistence
    # -----------------------------------------------------

    results = semantic_search(
        model,
        index,
        documents,
        query
    )

    # -----------------------------------------------------
    # Save FAISS index
    # -----------------------------------------------------

    print(
        "\n[5] Saving FAISS index to disk..."
    )

    faiss.write_index(
        index,
        "faiss_index.bin"
    )

    print(
        "FAISS index saved successfully."
    )

    print(
        "File: faiss_index.bin"
    )

    # -----------------------------------------------------
    # Save documents
    # -----------------------------------------------------

    np.save(
        "documents.npy",
        np.array(
            documents,
            dtype=object
        )
    )

    print(
        "Documents saved successfully."
    )

    print(
        "File: documents.npy"
    )

    # -----------------------------------------------------
    # Save embeddings
    # -----------------------------------------------------

    np.save(
        "embeddings.npy",
        embeddings
    )

    print(
        "Embeddings saved successfully."
    )

    print(
        "File: embeddings.npy"
    )

    # -----------------------------------------------------
    # Save search results
    # -----------------------------------------------------

    before_indices = [
        int(item[0])
        for item in results
    ]

    np.save(
        "before_results.npy",
        np.array(
            before_indices,
            dtype=np.int64
        )
    )

    print(
        "Before-persistence results "
        "saved successfully."
    )

    # -----------------------------------------------------
    # Completion
    # -----------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "FAISS INDEX CREATION AND PERSISTENCE COMPLETED"
    )

    print(
        "=" * 70
    )


# ---------------------------------------------------------
# Start program
# ---------------------------------------------------------

if __name__ == "__main__":

    main()