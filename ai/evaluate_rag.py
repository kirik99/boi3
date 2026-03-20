import os
import json
import logging
import sys
import io
from dotenv import load_dotenv
from datasets import Dataset
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas import evaluate
from ragas.metrics import answer_relevancy, faithfulness, context_precision, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from rag_pipeline import rag_query

# Force UTF-8 for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Configuration for DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("DEEPSEEK_API_KEY="):
                    DEEPSEEK_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except:
        pass

if not DEEPSEEK_API_KEY:
    print("ERROR: DEEPSEEK_API_KEY not found.")
    exit(1)

# Set environment variable for internal components
os.environ["OPENAI_API_KEY"] = DEEPSEEK_API_KEY

# Initialize DeepSeek LLM for Ragas
evaluator_llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)
ragas_llm = LangchainLLMWrapper(evaluator_llm)

# Initialize local HuggingFace Embeddings for Ragas metrics (avoids OpenAI/DeepSeek API issues)
print("Loading local embeddings model (HuggingFace)...")
evaluator_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
ragas_embeddings = LangchainEmbeddingsWrapper(evaluator_embeddings)

# 20 Test cases
test_cases = [
    {"query": "какое оборудование есть в лаборатории", "ground_truth": "Анализатор влажности (Shimadzu MOC-120H), Баня водяная (Loip lb-163), Колбонагреватель (LTH 500), Эвапоратор и др."},
    {"query": "что такое анализ пищевых продуктов согласно Food Analysis Fourth Edition?", "ground_truth": "Разработка и изучение аналитических процедур для оценки свойств продуктов и их ингредиентов."},
    {"query": "Что такое Proximate Analysis?", "ground_truth": "Система анализа основных компонентов пищи: влаги, золы, протеина, жира и углеводов."},
    {"query": "Что такое 'ash analysis'?", "ground_truth": "Определение минеральных веществ путем сжигания органики при высокой температуре."},
    {"query": "Меры предосторожности при работе с вытяжным шкафом (ШВЛ-0,5.5).", "ground_truth": "Проверка вентиляции, использование защитного экрана, отсутствие загромождения зоны."},
    {"query": "Как подготовить эвапоратор EV311H к работе?", "ground_truth": "Проверка герметичности, заливка воды в баню, настройка скорости вращения (согласно Rotary Evaporator User Manual)."},
    {"query": "Принцип работы Spectrophotometer Shimadzu UV 2600.", "ground_truth": "Измерение поглощения света в УФ и видимом диапазоне для определения концентрации веществ."},
    {"query": "Для чего нужна 'Тест Машина' (Data Processing Reference Manual)?", "ground_truth": "Для обработки данных испытаний, построения графиков и анализа физических свойств материалов."},
    {"query": "Как проводить калибровку в Shimadzu MOC-120H?", "ground_truth": "Использование калибровочных гирь и встроенных режимов настройки весов и температуры."},
    {"query": "Что описывает EZ-Brochure.pdf?", "ground_truth": "Описание возможностей и характеристик оборудования серии EZ (вероятно, испытательные машины)."},
    {"query": "Как строится калибровочный график согласно документам?", "ground_truth": "Путем измерения сигналов стандартных образцов с известной концентрацией и построения зависимости."},
    {"query": "Методика определения антиоксидантной активности DPPH.", "ground_truth": "Использование реагента DPPH для оценки способности образца нейтрализовать свободные радикалы."},
    {"query": "Как определяется фенол по методике в БД?", "ground_truth": "Спектрофотометрический или другой аналитический метод, описанный в соответствующих инструкциях."},
    {"query": "О чем пособие 'Практикум по оценке качества и безопасности продуктов'?", "ground_truth": "Методы ветеринарно-санитарной экспертизы и оценки безопасности сырья и продуктов."},
    {"query": "Зачем нужен UMP к лабораторным работам по безопасности сырья?", "ground_truth": "Учебно-методическое пособие для контроля качества продовольственного сырья и питания."},
    {"query": "Какие методы определения влажности описаны в 6-2-faqc-practicals?", "ground_truth": "Лабораторные методы контроля качества, включая сушку и специфические тесты."},
    {"query": "Параметры работы эвапоратора при удалении растворителей.", "ground_truth": "Температура бани, давление (вакуум) и скорость вращения колбы."},
    {"query": "Принципы ИК-спектроскопии в аналитике.", "ground_truth": "Анализ колебательных спектров молекул для идентификации компонентов."},
    {"query": "Что такое документ 4293768320.pdf?", "ground_truth": "Техническая документация или стандарт (согласно количеству чанков - объемный документ)."},
    {"query": "Список приборов в мануале 'Тест Машина Users Guide'.", "ground_truth": "Описание органов управления, программного обеспечения и режимов работы машины."}
]

def main():
    print(f"Starting RAG evaluation with {len(test_cases)} cases using DeepSeek and Local Embeddings...")
    
    questions = []
    answers = [] 
    contexts = []
    ground_truths = []
    
    for tc in test_cases:
        query = tc["query"]
        print(f"Processing query: {query}")
        response_data = rag_query(query)
        questions.append(query)
        ground_truths.append(tc["ground_truth"])
        
        results = response_data.get('results', [])
        context_list = [r.get('content', '') for r in results]
        contexts.append(context_list)
        
        # New: Generate concise answer using DeepSeek to improve Relevancy metric
        if context_list:
            context_str = "\n".join(context_list)[:3000]
            prompt = (
                "Answer the user query based ONLY on the provided context. "
                "Be extremely concise (1-3 sentences). "
                "If the context doesn't contain the answer, say 'Информация не найдена'.\n\n"
                f"Context:\n{context_str}\n\n"
                f"User Question: {query}\n\n"
                "Concise Answer (in Russian if appropriate):"
            )
            try:
                # Use the evaluator_llm but with a low token limit for efficiency
                # evaluator_llm is ChatOpenAI
                ai_msg = evaluator_llm.invoke(prompt, max_tokens=150)
                generated_answer = ai_msg.content.strip()
            except Exception as e:
                print(f"  Warning: Generation failed: {e}")
                generated_answer = "\n".join(context_list)[:500]
        else:
            generated_answer = "Информация не найдена."
            
        answers.append(generated_answer)
        print(f"  AI Answer: {generated_answer[:100]}...")
        
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    
    dataset = Dataset.from_dict(data)
    
    try:
        print("\nEvaluating metrics (this might take ~5-7 minutes)...")
        result = evaluate(
            dataset=dataset,
            metrics=[
                answer_relevancy,
                faithfulness,
                context_precision,
                context_recall
            ],
            llm=ragas_llm,
            embeddings=ragas_embeddings
        )
        
        print("\n=== RAGAS EVALUATION RESULTS ===")
        print(result)
        
        df = result.to_pandas()
        df.to_csv('ragas_evaluation_results.csv', index=False)
        print("\nDetailed results saved to 'ragas_evaluation_results.csv'")
    except Exception as e:
        print(f"\nEvaluation failed. Error: {e}")

if __name__ == "__main__":
    main()
