import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(path="/home/coden809/CHATTY/chroma_db")
collections = client.list_collections()

for coll in collections:
    print(f"Collection: {coll.name}")
    try:
        data = coll.get(limit=5)
        print(f"Items: {data['documents']}")
    except Exception as e:
        print(f"Error: {e}")
