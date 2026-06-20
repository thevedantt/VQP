import os
import json

def load_datasets(lq_path, dd_path):
    if not os.path.exists(lq_path):
        raise FileNotFoundError(f"Labeled questions dataset not found at {lq_path}")
    if not os.path.exists(dd_path):
        raise FileNotFoundError(f"Diagram dataset not found at {dd_path}")
        
    with open(lq_path, 'r', encoding='utf-8') as f:
        lq = json.load(f)
    with open(dd_path, 'r', encoding='utf-8') as f:
        dd = json.load(f)
    return lq, dd

def merge_datasets(lq, dd):
    all_q = {}
    for q in lq:
        all_q[q['question_id']] = q.copy()
        
    for q in dd:
        qid = q['question_id']
        if qid in all_q:
            if q.get('requires_diagram') is True:
                all_q[qid]['requires_diagram'] = True
            if q.get('diagram_type') and q.get('diagram_type') != 'none':
                all_q[qid]['diagram_type'] = q.get('diagram_type')
        else:
            all_q[qid] = q.copy()
            
    # Filter questions where requires_diagram is True
    diag_questions = [q for q in all_q.values() if q.get('requires_diagram') is True]
    return diag_questions

def classify_question(q):
    diagram_type = q.get('diagram_type', '').lower()
    chapter = q.get('chapter', '').lower() if q.get('chapter') else ''
    concept = q.get('concept', '').lower() if q.get('concept') else ''
    question_text = q.get('question', '').lower() if q.get('question') else ''
    
    # 1. Ray Optics
    if (diagram_type == 'ray_diagram' or 
        'ray optics' in chapter or 
        'optics' in chapter or
        'lens' in concept or 'lens' in question_text or
        'prism' in concept or 'prism' in question_text or
        'microscope' in concept or 'microscope' in question_text or
        'telescope' in concept or 'telescope' in question_text or
        'mirror' in concept or 'mirror' in question_text or
        'refraction' in concept or 'refraction' in question_text):
        return 'ray_optics'
        
    # 2. Circuits
    if (diagram_type in ('circuit', 'current_electricity') or 
        'circuit' in chapter or 'circuit' in concept or 'circuit' in question_text or
        'wheatstone' in concept or 'wheatstone' in question_text or
        'resistor' in concept or 'resistor' in question_text or
        'capacitor' in concept or 'capacitor' in question_text or
        'inductor' in concept or 'inductor' in question_text or
        'potentiometer' in concept or 'potentiometer' in question_text or
        'meter bridge' in concept or 'meter bridge' in question_text or
        'galvanometer' in concept or 'galvanometer' in question_text or
        'kirchhoff' in concept or 'kirchhoff' in question_text):
        return 'circuits'
        
    # 3. Magnetic Fields
    if (diagram_type == 'magnetic_field' or 
        'magnetism' in chapter or 'magnetic' in chapter or
        'magnetic field' in concept or 'magnetic field' in question_text or
        'solenoid' in concept or 'solenoid' in question_text or
        'magnet' in concept or 'magnet' in question_text or
        'cyclotron' in concept or 'cyclotron' in question_text):
        return 'magnetic_fields'
        
    # 4. Graphs
    if (diagram_type == 'graph' or 
        'graph' in concept or 'graph' in question_text or
        'plot' in concept or 'plot' in question_text or
        'variation of' in concept or 'variation of' in question_text or
        'curve' in concept or 'curve' in question_text):
        return 'graphs'
        
    # 5. Free Body
    if (diagram_type in ('free_body', 'fbd') or 
        'free body' in concept or 'free body' in question_text or
        'block' in question_text or 'pulley' in question_text or
        'friction' in question_text or 'tension' in question_text or
        'fbd' in question_text or 'force diagram' in question_text):
        return 'free_body'
        
    return None

def select_representative(questions):
    # Sort by question_id to be deterministic
    questions = sorted(questions, key=lambda x: x['question_id'])
    selected = []
    
    # We want to select 5 representative questions.
    for _ in range(5):
        if not questions:
            break
        best_candidate = None
        min_penalty = float('inf')
        
        for q in questions:
            if q in selected:
                continue
            penalty = 0
            
            # Penalty for concept overlap
            q_concept = q.get('concept')
            if q_concept and q_concept != 'None':
                for s in selected:
                    if s.get('concept') == q_concept:
                        penalty += 10
            
            # Penalty for difficulty overlap
            q_diff = q.get('difficulty')
            if q_diff:
                for s in selected:
                    if s.get('difficulty') == q_diff:
                        penalty += 2
                        
            # Penalty for type overlap
            q_type = q.get('type')
            if q_type:
                for s in selected:
                    if s.get('type') == q_type:
                        penalty += 2
            
            # Penalty for text similarity (Jaccard similarity of words)
            q_words = set(q.get('question', '').lower().split())
            for s in selected:
                s_words = set(s.get('question', '').lower().split())
                if q_words and s_words:
                    intersection = q_words.intersection(s_words)
                    union = q_words.union(s_words)
                    jaccard = len(intersection) / len(union)
                    penalty += jaccard * 5
                    
            if penalty < min_penalty:
                min_penalty = penalty
                best_candidate = q
                
        if best_candidate:
            selected.append(best_candidate)
            questions.remove(best_candidate)
            
    return selected

def main():
    lq_path = os.path.join('backend', 'app', 'data', 'question_bank', 'labeled_questions.json')
    dd_path = os.path.join('backend', 'app', 'data', 'question_bank', 'diagram_dataset.json')
    
    lq, dd = load_datasets(lq_path, dd_path)
    diag_questions = merge_datasets(lq, dd)
    
    # Group questions by category
    categories = {
        'ray_optics': [],
        'circuits': [],
        'magnetic_fields': [],
        'graphs': [],
        'free_body': []
    }
    
    for q in diag_questions:
        cat = classify_question(q)
        if cat in categories:
            categories[cat].append(q)
            
    # Select 5 representative questions per category
    seed_questions = {}
    for cat, qs in categories.items():
        selected_qs = select_representative(qs)
        seed_questions[cat] = []
        for q in selected_qs:
            # Format according to required structure
            seed_questions[cat].append({
                'question_id': q.get('question_id', ''),
                'question': q.get('question', ''),
                'chapter': q.get('chapter', '') if q.get('chapter') else '',
                'concept': q.get('concept', '') if q.get('concept') else '',
                'diagram_type': q.get('diagram_type', '') if q.get('diagram_type') else ''
            })
            
    # Export to backend/app/data/diagram_library/seed_questions.json
    export_dir = os.path.join('backend', 'app', 'data', 'diagram_library')
    os.makedirs(export_dir, exist_ok=True)
    
    export_path = os.path.join(export_dir, 'seed_questions.json')
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(seed_questions, f, indent=2, ensure_ascii=False)
        
    # Print summary
    print("====================================")
    print("DIAGRAM LIBRARY SEED DATASET")
    print("====================================")
    print(f"Ray Optics: {len(seed_questions['ray_optics'])}")
    print(f"Circuits: {len(seed_questions['circuits'])}")
    print(f"Magnetic Fields: {len(seed_questions['magnetic_fields'])}")
    print(f"Graphs: {len(seed_questions['graphs'])}")
    print(f"Free Body: {len(seed_questions['free_body'])}")
    total = sum(len(qs) for qs in seed_questions.values())
    print(f"Total: {total}")
    print("====================================")

if __name__ == '__main__':
    main()
