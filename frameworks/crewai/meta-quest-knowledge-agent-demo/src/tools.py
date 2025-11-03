"""Tools for the Meta Quest Knowledge Agent."""

import os
from pathlib import Path
from typing import List, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class KnowledgeBaseManager:
    """Manages the PDF knowledge base and vector store."""

    def __init__(self, knowledge_dir: str = "./knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.vector_store = None
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def load_documents(self) -> List:
        """Load PDF and text documents from the knowledge directory."""
        if not self.knowledge_dir.exists():
            raise ValueError(f"Knowledge directory not found: {self.knowledge_dir}")

        documents = []

        # Load PDF files
        try:
            pdf_loader = DirectoryLoader(
                str(self.knowledge_dir),
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=False,
            )
            pdf_docs = pdf_loader.load()
            documents.extend(pdf_docs)
        except Exception as e:
            print(f"Warning: Could not load PDF files: {e}")

        # Load text files
        try:
            txt_loader = DirectoryLoader(
                str(self.knowledge_dir),
                glob="**/*.txt",
                loader_cls=TextLoader,
                show_progress=False,
            )
            txt_docs = txt_loader.load()
            documents.extend(txt_docs)
        except Exception as e:
            print(f"Warning: Could not load text files: {e}")

        if not documents:
            raise ValueError(f"No documents found in {self.knowledge_dir}")

        # Split documents into chunks
        split_docs = self.text_splitter.split_documents(documents)
        return split_docs

    def create_vector_store(self):
        """Create FAISS vector store from documents."""
        documents = self.load_documents()
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        return self.vector_store

    def search(self, query: str, k: int = 5) -> List[str]:
        """Search the knowledge base for relevant information."""
        if self.vector_store is None:
            self.create_vector_store()

        results = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results]


# Global knowledge base manager
_kb_manager: Optional[KnowledgeBaseManager] = None


def get_knowledge_base_manager() -> KnowledgeBaseManager:
    """Get or create the global knowledge base manager."""
    global _kb_manager
    if _kb_manager is None:
        knowledge_dir = os.getenv("KNOWLEDGE_DIR", "./knowledge")
        _kb_manager = KnowledgeBaseManager(knowledge_dir)
    return _kb_manager


# Tool Input Schemas
class SearchDocsInput(BaseModel):
    """Input schema for searching Meta Quest docs."""
    query: str = Field(..., description="The search query or question about Meta Quest")


class SearchTopicInput(BaseModel):
    """Input schema for searching specific topic."""
    topic: str = Field(..., description="Specific topic to search for (e.g., 'controllers', 'setup', 'apps')")


# CrewAI Tool Implementations
class SearchMetaQuestDocsTool(BaseTool):
    name: str = "search_meta_quest_docs"
    description: str = "Search the Meta Quest documentation for information related to a query"
    args_schema: Type[BaseModel] = SearchDocsInput

    def _run(self, query: str) -> str:
        """Execute the search."""
        try:
            kb_manager = get_knowledge_base_manager()
            results = kb_manager.search(query, k=5)

            if not results:
                return "No relevant information found in the Meta Quest documentation."

            combined_results = "\n\n---\n\n".join(results)
            return f"Relevant information from Meta Quest documentation:\n\n{combined_results}"

        except Exception as e:
            return f"Error searching documentation: {str(e)}"


class GetMetaQuestOverviewTool(BaseTool):
    name: str = "get_meta_quest_overview"
    description: str = "Get a general overview of Meta Quest from the documentation"

    def _run(self) -> str:
        """Get overview information."""
        try:
            kb_manager = get_knowledge_base_manager()
            overview_query = "What is Meta Quest? Overview of Meta Quest features and capabilities"
            results = kb_manager.search(overview_query, k=3)

            if not results:
                return "No overview information found in the documentation."

            combined_results = "\n\n".join(results)
            return f"Meta Quest Overview:\n\n{combined_results}"

        except Exception as e:
            return f"Error retrieving overview: {str(e)}"


class SearchSpecificTopicTool(BaseTool):
    name: str = "search_specific_topic"
    description: str = "Search for information about a specific Meta Quest topic"
    args_schema: Type[BaseModel] = SearchTopicInput

    def _run(self, topic: str) -> str:
        """Search for a specific topic."""
        try:
            kb_manager = get_knowledge_base_manager()
            topic_query = f"Meta Quest {topic} information details features"
            results = kb_manager.search(topic_query, k=4)

            if not results:
                return f"No information found about {topic} in the documentation."

            combined_results = "\n\n---\n\n".join(results)
            return f"Information about {topic}:\n\n{combined_results}"

        except Exception as e:
            return f"Error searching for topic {topic}: {str(e)}"


# Export all tools
META_QUEST_TOOLS = [
    SearchMetaQuestDocsTool(),
    GetMetaQuestOverviewTool(),
    SearchSpecificTopicTool(),
]
