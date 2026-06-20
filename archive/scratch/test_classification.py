import json

lq_path = r'c:\CODES\VQP\backend\app\data\question_bank\labeled_questions.json'
dd_path = r'c:\CODES\VQP\backend\app\data\question_bank\diagram_dataset.json'

with open(lq_path, 'r', encoding='utf-8') as f:
    lq = json.load(f)

with open(dd_path, 'r', encoding='utf-8') as f:
    dd = json.load(f)

# Merge datasets
all_q = {}
for q in lq:
    all_q[q['question_id']] = q.copy()

for q in dd:
    qid = q['question_id']
    if qid in all_q:
        # Merge, keeping lq's fields, but if dd has requires_diagram = True, we set it.
        # Let's see if we should prioritize dd's diagram_type if it is not none.
        if q.get('requires_diagram') is True:
            all_q[qid]['requires_diagram'] = True
        if q.get('diagram_type') and q.get('diagram_type') != 'none':
            all_q[qid]['diagram_type'] = q.get('diagram_type')
    else:
        all_q[qid] = q.copy()

diag_questions = [q for q in all_q.values() if q.get('requires_diagram') is True]

print(f"Total questions with requires_diagram = True: {len(diag_questions)}")

# Let's write a simple classification function and see how it fares on all 65 questions.
def classify(q):
    diagram_type = q.get('diagram_type', '').lower()
    chapter = q.get('chapter', '').lower()
    concept = q.get('concept', '').lower()
    question_text = q.get('question', '').lower()
    
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
    if (diagram_type == 'circuit' or 
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

classified = {}
unclassified = []
for q in diag_questions:
    cat = classify(q)
    if cat:
        classified.setdefault(cat, []).append(q)
    else:
        unclassified.append(q)

for cat, qs in classified.items():
    print(f"\nCategory {cat}: {len(qs)} questions")
    for q in qs[:3]:
        print(f"  ID: {q['question_id']}, diagram_type: {q.get('diagram_type')}, chapter: {q.get('chapter')}, concept: {q.get('concept')}")

print(f"\nUnclassified: {len(unclassified)} questions")
for q in unclassified:
    print(f"  ID: {q['question_id']}, diagram_type: {q.get('diagram_type')}, chapter: {q.get('chapter')}, concept: {q.get('concept')}, text: {repr(q.get('question'))[:100]}")
