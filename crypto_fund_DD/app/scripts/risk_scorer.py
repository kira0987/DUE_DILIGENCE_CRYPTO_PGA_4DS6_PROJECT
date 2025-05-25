import json
from scripts.evaluate_investor_risk import evaluate_investor_risk

def score_investment(answers):
    """
    Compute risk scores per category and global total based on critical questions only.
    Args:
        answers (dict): {question_id (int): answer (str)}
    Returns:
        dict: {category_name: score_percentage, ..., 'TOTAL': total_score}
    """

    # 1. Load Critical Questions INSIDE function
    with open("data/critical_questions.json", "r", encoding="utf-8") as f:
        critical_questions = json.load(f)

    category_scores = {}
    category_weights = {}

    for cq in critical_questions:
        q_id = cq['id']
        category = cq['category']
        question_weight = cq['weight']

        if q_id not in answers:
            continue  # Skip if no answer

        answer = answers[q_id]
        evaluation = evaluate_investor_risk(answer)

        # Map evaluation to numeric risk score
        if evaluation.lower() == "positive":
            score = 0.0
        elif evaluation.lower() == "partial":
            score = 0.5
        else:  # negative or missing
            score = 1.0

        # Initialize category aggregates if needed
        if category not in category_scores:
            category_scores[category] = 0.0
            category_weights[category] = 0.0

        category_scores[category] += score * question_weight
        category_weights[category] += question_weight

    # Calculate category-level scores
    final_scores = {}
    for category, total_score in category_scores.items():
        if category_weights[category] == 0:
            final_scores[category] = 0.0
        else:
            final_scores[category] = round((total_score / category_weights[category]) * 100, 2)

    # Calculate overall global score
    total_score = sum(category_scores.values())
    total_weight = sum(category_weights.values())

    if total_weight == 0:
        global_score = 0.0
    else:
        global_score = round((total_score / total_weight) * 100, 2)

    final_scores['TOTAL'] = global_score

    return final_scores
