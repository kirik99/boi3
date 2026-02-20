#!/usr/bin/env python3
"""
Seed script for Supabase database.
Adds test documents with embeddings.

Usage: python seed_data.py
"""

from supabase_client import supabase
from embedding import get_embedding
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Test documents for the laboratory
documents = [
    {
        "title": "PCR Analysis Method",
        "doc_type": "method",
        "full_text": "Polymerase Chain Reaction (PCR) is a molecular biology method used to amplify specific DNA regions. Requires thermostable DNA polymerase, primers, and nucleotides.",
    },
    {
        "title": "DNA Extraction Protocol",
        "doc_type": "protocol",
        "full_text": "DNA extraction from biological material includes cell lysis, protein removal, and nucleic acid precipitation. Uses phenol-chloroform extraction or silica membranes.",
    },
    {
        "title": "Laboratory Safety Guidelines",
        "doc_type": "safety",
        "full_text": "When working in the laboratory, use personal protective equipment: gloves, lab coat, safety goggles. Eating and drinking in the work area is prohibited.",
    },
    {
        "title": "Spectrophotometer Calibration",
        "doc_type": "method",
        "full_text": "Before measuring DNA concentration, calibrate the spectrophotometer with a blank cuvette containing buffer solution. Measurements are taken at 260 nm wavelength.",
    },
    {
        "title": "Reaction Mixture Preparation",
        "doc_type": "protocol",
        "full_text": "For a 25 μl PCR reaction: 12.5 μl master mix, 1 μl forward primer, 1 μl reverse primer, 5 μl template DNA, 5.5 μl deionized water.",
    },
]

print("Adding documents with embeddings to Supabase...")
print("-" * 50)

added_count = 0
for doc in documents:
    try:
        # Get embedding
        embedding = get_embedding(doc["full_text"])
        
        # Add document to Supabase
        res = supabase.table("documents").insert({
            "title": doc["title"],
            "doc_type": doc["doc_type"],
            "full_text": doc["full_text"],
            "embedding": embedding,
        }).execute()
        
        print(f"✓ Added: {doc['title']}")
        added_count += 1
        
    except Exception as e:
        print(f"✗ Failed to add '{doc['title']}': {e}")

print("-" * 50)
print(f"✅ Successfully added {added_count}/{len(documents)} documents!")

if added_count == len(documents):
    print("\nAll documents seeded successfully!")
else:
    print("\nSome documents failed to seed. Check the errors above.")
    sys.exit(1)
