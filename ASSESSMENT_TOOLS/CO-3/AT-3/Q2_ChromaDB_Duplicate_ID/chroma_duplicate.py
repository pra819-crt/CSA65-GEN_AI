import chromadb


# ---------------------------------------------------------
# Create ChromaDB client
# ---------------------------------------------------------

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_or_create_collection(
    name="document_collection"
)


# ---------------------------------------------------------
# Documents
# ---------------------------------------------------------

documents = [
    "Artificial Intelligence is used in healthcare, education, finance, and transportation.",
    "Machine Learning allows computers to learn patterns from data and make predictions.",
    "Generative AI can create text, images, code, and other types of content.",
    "Natural Language Processing helps computers understand and process human language.",
    "Computer Vision enables computers to analyze and understand images and videos."
]


# ---------------------------------------------------------
# Part 1: Demonstrate duplicate ID problem
# ---------------------------------------------------------

print("=" * 70)
print("       CHROMADB DUPLICATE-ID DEBUGGING")
print("=" * 70)

print("\n[1] Attempting insertion with duplicate IDs...")

duplicate_ids = [
    "doc1",
    "doc1",
    "doc1",
    "doc1",
    "doc1"
]

try:

    collection.add(
        ids=duplicate_ids,
        documents=documents
    )

    print("Documents inserted successfully.")

except Exception as e:

    print("\nDUPLICATE-ID ERROR DETECTED!")
    print("Problem:", e)


# ---------------------------------------------------------
# Part 2: Generate unique IDs
# ---------------------------------------------------------

print("\n[2] Generating unique document IDs...")

unique_ids = [
    f"doc_{i + 1:03d}"
    for i in range(len(documents))
]

print("Generated IDs:")

for doc_id in unique_ids:
    print(doc_id)


# ---------------------------------------------------------
# Part 3: Insert using unique IDs
# ---------------------------------------------------------

print("\n[3] Inserting documents using unique IDs...")

try:

    collection.add(
        ids=unique_ids,
        documents=documents
    )

    print("Documents inserted successfully!")
    print("Number of documents:", len(documents))

except Exception as e:

    print("ERROR:", e)


# ---------------------------------------------------------
# Part 4: Semantic retrieval
# ---------------------------------------------------------

print("\n[4] Performing document retrieval...")

query = input(
    "\nEnter your search query: "
).strip()

if not query:

    print("ERROR: Query cannot be empty.")

else:

    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    print("\nTop Retrieved Documents:")

    retrieved_documents = results["documents"][0]
    retrieved_ids = results["ids"][0]

    for i in range(len(retrieved_documents)):

        print("\nRank", i + 1)
        print("Document ID:", retrieved_ids[i])
        print("Document:", retrieved_documents[i])


# ---------------------------------------------------------
# Completion
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("CHROMADB DUPLICATE-ID TEST COMPLETED")
print("=" * 70)