import json
import os

lq_path = r'c:\CODES\VQP\backend\app\data\question_bank\labeled_questions.json'
dd_path = r'c:\CODES\VQP\backend\app\data\question_bank\diagram_dataset.json'

with open(lq_path, 'r', encoding='utf-8') as f:
    lq = json.load(f)

with open(dd_path, 'r', encoding='utf-8') as f:
    dd = json.load(f)

# Let's inspect requires_diagram
print("lq requires_diagram values:")
lq_diag_types = {}
for q in lq:
    req = q.get('requires_diagram')
    dtype = q.get('diagram_type')
    lq_diag_types[dtype] = lq_diag_types.get(dtype, 0) + 1
print(lq_diag_types)

print("dd requires_diagram values:")
dd_diag_types = {}
for q in dd:
    req = q.get('requires_diagram')
    dtype = q.get('diagram_type')
    dd_diag_types[dtype] = dd_diag_types.get(dtype, 0) + 1
print(dd_diag_types)

# Let's see the union of all questions where requires_diagram = True
all_q = {}
for q in lq:
    all_q[q['question_id']] = q.copy()

for q in dd:
    qid = q['question_id']
    if qid in all_q:
        all_q[qid].update(q)
    else:
        all_q[qid] = q.copy()

diag_questions = [q for q in all_q.values() if q.get('requires_diagram') is True]
print(f"Total merged questions with requires_diagram = True: {len(diag_questions)}")

# Let's inspect chapters, concepts, and diagram_types of these questions
print("\nDiagram types of diag_questions:")
dtypes = {}
for q in diag_questions:
    dt = q.get('diagram_type')
    dtypes[dt] = dtypes.get(dt, 0) + 1
print(dtypes)

print("\nChapters of diag_questions:")
chapters = {}
for q in diag_questions:
    ch = q.get('chapter', 'None')
    chapters[ch] = chapters.get(ch, 0) + 1
print(chapters)

print("\nConcepts of diag_questions:")
concepts = {}
for q in diag_questions:
    con = q.get('concept', 'None')
    concepts[con] = concepts.get(con, 0) + 1
for k, v in list(concepts.items())[:30]:
    print(f"  {k}: {v}")
