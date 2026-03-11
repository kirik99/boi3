import os
import json
import logging
from dotenv import load_dotenv
from datasets import Dataset
try:
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, faithfulness, context_precision, context_recall
except ImportError:
    print("Ragas is not installed. Please run: pip install ragas datasets")
    exit(1)

from rag_pipeline import rag_query

load_dotenv()

logging.basicConfig(level=logging.INFO)

# We need an LLM for RAGAS evaluation. By default it uses OpenAI.
if "OPENAI_API_KEY" not in os.environ:
    print("WARNING: OPENAI_API_KEY is not set. Ragas uses OpenAI by default for evaluation metrics.")
    print("Please set OPENAI_API_KEY in your .env file or environment variables to run this evaluation.")

# Sample test cases
test_cases = [
    {
        "query": "какое оборудование есть в лаборатории",
        "ground_truth": "В лаборатории должно быть специальное оборудование, которое описано в списке."
    },
    {
        "query": "как откалибровать прибор?",
        "ground_truth": "Для калибровки следуйте инструкции производителя и используйте стандартные образцы."
    }
]

def main():
    print("Starting RAG evaluation with Ragas...")
    
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    for tc in test_cases:
        query = tc["query"]
        print(f"\nProcessing query: {query}")
        
        # Call existing RAG pipeline
        response = rag_query(query)
        
        questions.append(query)
        ground_truths.append(tc["ground_truth"])
        
        results = response.get('results', [])
        
        # Combine contexts
        context_list = [r.get('content', '') for r in results]
        contexts.append(context_list)
        
        # Our RAG pipeline retrieves chunks. If there is a final generative LLM step, replace this with its output.
        generated_answer = "\n".join(context_list)[:1000] if context_list else "No answer found"
        answers.append(generated_answer)
        
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    
    dataset = Dataset.from_dict(data)
    print("\nDataset for Evaluation:")
    for idx, row in enumerate(dataset):
        print(f"[{idx}] Question: {row['question']}")
        print(f"[{idx}] Contexts: {len(row['contexts'])}")
    
    # Run evaluation
    try:
        print("\nEvaluating metrics (This may take some time depending on API limits)...")
        # For full usage you might need to adapt the metric configurations for Russian language
        # Provide the list of metrics
        result = evaluate(
            dataset=dataset,
            metrics=[
                answer_relevancy,
                faithfulness,
                context_precision,
                context_recall
            ]
        )
        
        print("\n=== RAGAS EVALUATION RESULTS ===")
        print(result)
        
        # Save results
        df = result.to_pandas()
        df.to_csv('ragas_evaluation_results.csv', index=False)
        print("\nResults saved to ragas_evaluation_results.csv")
    except Exception as e:
        print(f"\nEvaluation failed. \nError: {e}\nDid you set OPENAI_API_KEY? Ragas requires an evaluator LLM by default.")

if __name__ == "__main__":
    main()
