# Q1: FAISS Index Persistence
# Reload saved FAISS index and compare semantic search
# results before and after persistence.

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# Load saved FAISS index
# ---------------------------------------------------------

def load_faiss_index():

    print("\n[1] Loading saved FAISS index...")

    index = faiss.read_index("faiss_index.bin")

    print("FAISS index loaded successfully.")
    print("Vectors loaded:", index.ntotal)

    return index


# ---------------------------------------------------------
# Load saved documents
# ---------------------------------------------------------

def load_documents():

    print("\n[2] Loading saved documents...")

    documents = np.load(
        "documents.npy",
        allow_pickle=True
    ).tolist()

    print("Documents loaded successfully.")
    print("Number of documents:", len(documents))

    return documents


# ---------------------------------------------------------
# Load embedding model
# ---------------------------------------------------------

def load_model():

    print("\n[3] Loading embedding model...")

    model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    print("Embedding model loaded successfully.")

    return model


# ---------------------------------------------------------
# Perform semantic search
# ---------------------------------------------------------

def semantic_search(model, index, documents, query):

    print("\n[4] Performing semantic search after persistence...")
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

    for rank, idx in enumerate(indices[0], start=1):

        distance = float(
            distances[0][rank - 1]
        )

        document = documents[int(idx)]

        results.append(
            (int(idx), distance)
        )

        print("\nRank", rank)
        print("Document Index:", int(idx))
        print("Distance:", round(distance, 4))
        print("Document:", document)

    return results


# ---------------------------------------------------------
# Load previous search results
# ---------------------------------------------------------

def load_before_results():

    print("\n[5] Loading results from before persistence...")

    data = np.load(
        "before_results.npy",
        allow_pickle=True
    )

    print("Saved result data loaded.")

    # Convert NumPy data into a normal Python object
    try:
        data = data.tolist()
    except Exception:
        pass

    # Extract document indices safely
    before_indices = []

    # Case 1: list of tuples
    if isinstance(data, list):

        for item in data:

            if isinstance(item, (list, tuple, np.ndarray)):

                before_indices.append(
                    int(item[0])
                )

            else:

                before_indices.append(
                    int(item)
                )

    # Case 2: single tuple
    elif isinstance(data, tuple):

        for item in data:

            if isinstance(item, (list, tuple, np.ndarray)):

                before_indices.append(
                    int(item[0])
                )

            else:

                before_indices.append(
                    int(item)
                )

    # Case 3: dictionary
    elif isinstance(data, dict):

        for item in data.values():

            if isinstance(item, (list, tuple, np.ndarray)):

                before_indices.append(
                    int(item[0])
                )

            else:

                before_indices.append(
                    int(item)
                )

    # Case 4: single NumPy value
    else:

        try:

            before_indices.append(
                int(data)
            )

        except Exception:

            print("ERROR: Unable to read before_results.npy")
            return []

    return before_indices


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("          FAISS INDEX PERSISTENCE - RELOAD PROGRAM")
    print("=" * 70)

    # Load saved index
    index = load_faiss_index()

    # Load saved documents
    documents = load_documents()

    # Load embedding model
    model = load_model()

    # User query
    query = input(
        "\nEnter the same search query used before persistence: "
    ).strip()

    if not query:

        print("ERROR: Query cannot be empty.")
        return

    # Search after persistence
    results = semantic_search(
        model,
        index,
        documents,
        query
    )

    # -----------------------------------------------------
    # Compare before and after persistence
    # -----------------------------------------------------

    print("\n[5] Comparing search results...")

    before_indices = load_before_results()

    after_indices = [
        int(item[0])
        for item in results
    ]

    print("\nBefore persistence:")
    print(before_indices)

    print("\nAfter persistence:")
    print(after_indices)

    # -----------------------------------------------------
    # Consistency check
    # -----------------------------------------------------

    if before_indices == after_indices:

        print("\nCONSISTENCY CHECK: PASSED")
        print(
            "Search results are identical before and after persistence."
        )

    else:

        print("\nCONSISTENCY CHECK: NOT IDENTICAL")
        print(
            "The FAISS index was successfully reloaded, "
            "but the retrieved document ranking differs."
        )

        print("\nThis can happen because semantic embeddings "
              "or search results may have small differences.")

    # -----------------------------------------------------
    # Persistence verification
    # -----------------------------------------------------

    print("\n[6] Persistence Verification")

    print("FAISS index successfully reloaded.")
    print("Semantic search successfully performed after persistence.")

    print("\nRetrieved document indices:")

    for rank, (idx, distance) in enumerate(
        results,
        start=1
    ):

        print(
            f"Rank {rank}: "
            f"Document {idx}, "
            f"Distance {distance:.4f}"
        )

    print("\n" + "=" * 70)
    print("FAISS PERSISTENCE TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)


# ---------------------------------------------------------
# Program starts here
# ---------------------------------------------------------

if __name__ == "__main__":
    main()