"""Load method cards from YAML files into LanceDB vector store.

This replaces the raw document chunking approach with structured method cards.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.method_card import MethodCard, MethodCategory, ProblemType, DataConditions
from src.rag.vector_store import get_vector_store
from src.utils.embedding_factory import get_embeddings
from src.config import Config


def load_yaml_cards(yaml_file: Path) -> List[MethodCard]:
    """Load method cards from YAML file.
    
    Args:
        yaml_file: Path to YAML file containing method cards
        
    Returns:
        List of MethodCard objects
    """
    print(f"\n📂 Loading cards from: {yaml_file.name}")
    
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    
    cards = []
    for card_data in data:
        try:
            # Convert string enums to Enum objects
            card_data['category'] = MethodCategory(card_data['category'])
            card_data['problem_type'] = ProblemType(card_data['problem_type'])
            
            # Convert data_conditions dict to DataConditions object
            card_data['data_conditions'] = DataConditions(**card_data['data_conditions'])
            
            card = MethodCard(**card_data)
            cards.append(card)
            print(f"  ✓ {card.method_name} ({card.category.value})")
            
        except Exception as e:
            print(f"  ✗ Error loading card: {e}")
            continue
    
    return cards


def load_all_method_cards(cards_dir: Path) -> List[MethodCard]:
    """Load all method cards from directory.
    
    Args:
        cards_dir: Directory containing YAML card files
        
    Returns:
        List of all MethodCard objects
    """
    all_cards = []
    
    yaml_files = sorted(cards_dir.glob("*.yaml"))
    
    if not yaml_files:
        print(f"⚠️  No YAML files found in {cards_dir}")
        return []
    
    print(f"📚 Found {len(yaml_files)} YAML files")
    
    for yaml_file in yaml_files:
        cards = load_yaml_cards(yaml_file)
        all_cards.extend(cards)
    
    return all_cards


def store_cards_in_lancedb(cards: List[MethodCard], config: Config):
    """Store method cards in LanceDB vector store.
    
    Args:
        cards: List of MethodCard objects
        config: Application config
    """
    print(f"\n🗄️  Storing {len(cards)} method cards in LanceDB...")
    
    # Get embedding model
    embedding_model = get_embeddings()
    
    # Create LanceDB vector store directly with method_cards table
    from src.rag.vector_store import LanceDBVectorStore
    vector_store = LanceDBVectorStore(
        embeddings=embedding_model,
        table_name="method_cards"
    )
    
    # Convert cards to documents format
    from langchain_core.documents import Document
    import json
    
    documents = []
    for card in cards:
        doc = Document(
            page_content=card.to_embedding_text(),
            metadata=card.to_metadata()
        )
        # Store full card as JSON in metadata for retrieval
        doc.metadata["card_json"] = json.dumps(card.to_dict())
        documents.append(doc)
    
    # Add to vector store
    try:
        vector_store.add_documents(documents)
        print(f"✅ Successfully stored {len(documents)} method cards")
        
        # Verify storage with improved test query
        test_query = "how to handle missing values"
        results = vector_store.similarity_search(test_query, k=3)
        print(f"\n🔍 Test query: '{test_query}'")
        if results:
            top_result = results[0]
            # Extract method name from metadata_json or direct metadata
            method_name = top_result.metadata.get('method_name')
            if not method_name and 'metadata_json' in top_result.metadata:
                import json
                try:
                    meta = json.loads(top_result.metadata['metadata_json'])
                    method_name = meta.get('method_name', 'Unknown')
                except:
                    method_name = 'Unknown'
            print(f"   ✅ Top result: {method_name or 'Unknown'}")
            print(f"   Found {len(results)} relevant methods")
        else:
            print(f"   ⚠️  No results found")
        
    except Exception as e:
        print(f"❌ Error storing cards: {e}")
        raise


def print_summary(cards: List[MethodCard]):
    """Print summary of loaded cards."""
    print("\n" + "="*60)
    print("📊 METHOD CARD SUMMARY")
    print("="*60)
    
    # Count by category
    from collections import Counter
    categories = Counter(card.category.value for card in cards)
    
    print(f"\n📈 Total Cards: {len(cards)}")
    print("\n📑 By Category:")
    for category, count in sorted(categories.items()):
        print(f"   {category}: {count}")
    
    # List all methods
    print("\n📋 All Methods:")
    for card in sorted(cards, key=lambda c: (c.category.value, c.method_name)):
        package = card.python_package or card.library or ""
        print(f"   • {card.method_name:30s} ({package})")
    
    print("\n" + "="*60)


def main():
    """Load method cards and store in LanceDB."""
    print("="*60)
    print("🚀 METHOD CARD LOADER")
    print("="*60)
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    cards_dir = project_root / "method_cards"
    lancedb_dir = project_root / "lancedb" / "method_cards.lance"

    # Delete existing LanceDB method_cards.lance directory for a clean index
    if lancedb_dir.exists():
        import shutil
        print(f"🧹 Removing existing LanceDB directory: {lancedb_dir}")
        shutil.rmtree(lancedb_dir)
        print(f"✅ Removed {lancedb_dir}")

    if not cards_dir.exists():
        print(f"❌ Cards directory not found: {cards_dir}")
        return
    
    # Load configuration
    config = Config()
    
    cards = load_all_method_cards(cards_dir)

    if not cards:
        print("❌ No cards loaded")
        return

    # Deduplicate by method_name
    seen = set()
    deduped_cards = []
    for card in cards:
        if card.method_name not in seen:
            deduped_cards.append(card)
            seen.add(card.method_name)
    if len(deduped_cards) < len(cards):
        print(f"⚠️  Removed {len(cards) - len(deduped_cards)} duplicate cards by method_name.")
    cards = deduped_cards

    # Print summary
    print_summary(cards)

    # Store in LanceDB
    store_cards_in_lancedb(cards, config)

    print("\n✅ Method cards loaded successfully!")
    print(f"📍 Location: ./lancedb/method_cards.lance")

    # Instructions
    print("\n" + "="*60)
    print("📝 USAGE:")
    print("="*60)
    print("1. Method cards stored in: ./lancedb/method_cards.lance")
    print("2. Query using RAGSystem.retrieve_method_cards()")
    print("3. See method_cards/README.md for documentation")
    print("4. Run python testing/test_method_card_retrieval.py to validate")
    print("="*60)


if __name__ == "__main__":
    main()
