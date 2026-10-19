from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from .config import DOCUMENTS_DIR

from langchain_core.documents import Document

def load_documents():
    documents = []

    # Load PDFs
    pdf_dir = DOCUMENTS_DIR / "pdf"

    if pdf_dir.exists():
        for path in pdf_dir.rglob("*.pdf"):
            try:
                loader = PyPDFLoader(str(path))
                pages = loader.load()

                for page in pages:
                    page.metadata.update({
                        "type": "document",
                        "format": "pdf",
                        "source": str(
                            path.relative_to(DOCUMENTS_DIR)
                        ),
                    })

                documents.extend(pages)

            except Exception as error:
                print(f"Failed to load {path}: {error}")

    # Load DOCX files
    docx_dir = DOCUMENTS_DIR / "docx"

    if docx_dir.exists():
        for path in docx_dir.rglob("*.docx"):
            try:
                loader = Docx2txtLoader(str(path))
                docs = loader.load()

                for doc in docs:
                    doc.metadata.update({
                        "type": "document",
                        "format": "docx",
                        "source": str(
                            path.relative_to(DOCUMENTS_DIR)
                        ),
                    })

                documents.extend(docs)

            except Exception as error:
                print(f"Failed to load {path}: {error}")

    # Load Markdown files
    markdown_dir = DOCUMENTS_DIR / "markdown"

    if markdown_dir.exists():
        for path in markdown_dir.rglob("*.md"):
            try:
                text = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

                if not text.strip():
                    continue

                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "type": "document",
                            "format": "markdown",
                            "source": str(
                                path.relative_to(DOCUMENTS_DIR)
                            ),
                        },
                    )
                )

            except Exception as error:
                print(f"Failed to load {path}: {error}")

    print(f"Loaded {len(documents)} document pages/files.")
    
    # Split the extracted text into smaller chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} document chunks.")

    return chunks

