from .ingest import create_vector_store


def get_vector_store():
    return create_vector_store()


def search(
    query,
    k=6,
    source_type=None,
):
    vector_store = get_vector_store()

    if source_type:
        results = vector_store.similarity_search(
            query,
            k=k,
            filter={"type": source_type},
        )
    else:
        results = vector_store.similarity_search(
            query,
            k=k,
        )

    return results