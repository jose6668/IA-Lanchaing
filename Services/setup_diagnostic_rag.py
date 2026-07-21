import shutil
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_core import documents
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from Models.config import *


class DiagnosticDocumentProcessor:
    """
    Procesa el reporte educativo y crea una base vectorial
    persistente con ChromaDB.
    """

    def __init__(
        self,
        pdf_path: Path = DIAGNOSTIC_PDF_PATH,
        chroma_path: Path = DIAGNOSTIC_CHROMA_PATH,
    ) -> None:
        self.pdf_path = Path(pdf_path)
        self.chroma_path = Path(chroma_path)

        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDINGS_MODEL
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=120,
            length_function=len,
            separators=[
                "\n\n",
                "\n",
                ". ",
                "! ",
                "? ",
                " ",
                "",
            ],
        )

    def validate_pdf(self) -> None:
        """Comprueba que el PDF exista."""

        if not self.pdf_path.exists():
            raise FileNotFoundError(
                "No se encontró el PDF diagnóstico en:\n"
                f"{self.pdf_path}"
            )

        if self.pdf_path.suffix.lower() != ".pdf":
            raise ValueError(
                "El documento diagnóstico debe ser un PDF."
            )

    def load_document(self) -> list[Document]:
        self.validate_pdf()

        loader = PyPDFLoader(str(self.pdf_path))
        documents = loader.load()

        print(f"Páginas extraídas: {len(documents)}")

        for index, document in enumerate(documents, start=1):
            print(
                f"Página {index}: "
                f"{len(document.page_content)} caracteres"
            )

            document.metadata.update(
                {
                    "filename": self.pdf_path.name,
                    "document_type": "diagnostico_estudiantil",
                    "page_number": index,
                    "source": str(self.pdf_path),
                }
            )


        return documents

    def split_documents(
        self,
        documents: list[Document],
    ) -> list[Document]:
        """Divide las páginas en fragmentos recuperables."""

        chunks = self.text_splitter.split_documents(
            documents
        )

        for index, chunk in enumerate(chunks):
            chunk.metadata.update(
                {
                    "chunk_id": index,
                    "chunk_size": len(
                        chunk.page_content
                    ),
                }
            )

        print(
            f"✅ Fragmentos generados: {len(chunks)}"
        )

        return chunks

    def remove_existing_vectorstore(self) -> None:
        """Elimina el índice anterior para evitar duplicados."""

        if self.chroma_path.exists():
            print(
                "🗑️ Eliminando índice diagnóstico anterior..."
            )

            shutil.rmtree(
                self.chroma_path,
                ignore_errors=True,
            )

    def create_vectorstore(
        self,
        chunks: list[Document],
    ) -> Chroma:
        """Crea la colección vectorial."""

        if not chunks:
            raise ValueError(
                "No existen fragmentos para indexar."
            )

        self.remove_existing_vectorstore()

        print(
            "🔄 Creando base vectorial del diagnóstico..."
        )

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(
                self.chroma_path
            ),
            collection_name=(
                DIAGNOSTIC_COLLECTION_NAME
            ),
        )

        print(
            "✅ Base vectorial creada correctamente."
        )

        return vectorstore

    def setup(self) -> Chroma:
        """Ejecuta el procesamiento completo."""

        documents = self.load_document()
        chunks = self.split_documents(documents)
        vectorstore = self.create_vectorstore(
            chunks
        )

        print(
            f"📁 Índice guardado en: "
            f"{self.chroma_path}"
        )

        return vectorstore


def main() -> None:
    try:
        processor = DiagnosticDocumentProcessor()
        processor.setup()

        print("\n✅ Diagnóstico configurado exitosamente.")

    except Exception as error:
        print(
            "\n❌ No fue posible configurar "
            f"el diagnóstico: {error}"
        )

        raise


if __name__ == "__main__":
    main()