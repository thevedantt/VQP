import json

lq_path = r'c:\CODES\VQP\backend\app\data\question_bank\labeled_questions.json'
dd_path = r'c:\CODES\VQP\backend\app\data\question_bank\diagram_dataset.json'

with open(lq_path, 'r', encoding='utf-8') as f:
    lq = json.load(f)

with open(dd_path, 'r', encoding='utf-8') as f:
    dd = json.load(f)

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

diag_questions = [q for q in all_q.values() if q.get('requires_diagram') is True]

def classify(q):
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

categories = {
    'ray_optics': [],
    'circuits': [],
    'magnetic_fields': [],
    'graphs': [],
    'free_body': []
}

for q in diag_questions:
    cat = classify(q)
    if cat:
        categories[cat].append(q)

for cat, qs in categories.items():
    print(f"\n=================== {cat.upper()} ({len(qs)} questions) ===================")
    for q in qs:
        print(f"ID: {q['question_id']} | Concept: {q.get('concept')} | Diff: {q.get('difficulty')} | Type: {q.get('type')}")
        print(f"  Q: {repr(q['question'])[:150]}")
