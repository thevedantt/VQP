# Database Schemas

## documents

| Field | Type |
|---------|---------|
| id | UUID |
| title | TEXT |
| source | TEXT |
| content | TEXT |

## chunks

| Field | Type |
|---------|---------|
| id | UUID |
| document_id | UUID |
| chunk_text | TEXT |
| embedding | VECTOR |
| chapter | TEXT |
| topic | TEXT |
| subtopic | TEXT |

## knowledge_graph

| Field | Type |
|---------|---------|
| id | UUID |
| parent | TEXT |
| child | TEXT |
| relation | TEXT |

## generated_papers

| Field | Type |
|---------|---------|
| id | UUID |
| subject | TEXT |
| chapter | TEXT |
| paper_json | JSONB |
| created_at | TIMESTAMP |

## diagrams

| Field | Type |
|---------|---------|
| id | UUID |
| question_id | UUID |
| diagram_type | TEXT |
| diagram_path | TEXT |

## logs

| Field | Type |
|---------|---------|
| id | UUID |
| event | TEXT |
| status | TEXT |
| timestamp | TIMESTAMP |