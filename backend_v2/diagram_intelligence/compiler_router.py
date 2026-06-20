import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(BASE / "backend_v2"))
sys.path.insert(0, str(BASE))

for sub in [
    "ray", "circuit", "fbd",
    "magnetic_field", "semiconductor", "graph"
]:
    sys.path.insert(0, str(BASE / "approch2" / sub))

from diagram_intelligence.classifier.llm_classifier import (
    DiagramClassifier
)

from diagram_intelligence.blueprint_generator.blueprint_generator import (
    BlueprintGenerator
)

from diagram_intelligence.blueprint_evaluator import (
    BlueprintEvaluator
)


OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent
    / "compiled_output"
)

OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUTV2_DIR = (
    Path(__file__).resolve().parent.parent
    / "outputv2"
)

RAW_BLUEPRINT_DIR = (
    OUTPUTV2_DIR / "raw_blueprints"
)

ENHANCED_BLUEPRINT_DIR = (
    OUTPUTV2_DIR / "enhanced_blueprints"
)

EVALUATION_REPORT_DIR = (
    OUTPUTV2_DIR / "evaluation_reports"
)

COMPILED_SVG_DIR = (
    OUTPUTV2_DIR / "compiled_svgs"
)

for d in [
    RAW_BLUEPRINT_DIR,
    ENHANCED_BLUEPRINT_DIR,
    EVALUATION_REPORT_DIR,
    COMPILED_SVG_DIR
]:
    d.mkdir(parents=True, exist_ok=True)

SCHEMA_DIR = (
    Path(__file__).resolve().parent.parent
    / "schemas"
)


def _merge_schema(blueprint, family):

    schema_file = (
        SCHEMA_DIR / family / f"{family}_schema.json"
    )

    if not schema_file.exists():
        return blueprint

    with open(
        schema_file,
        "r",
        encoding="utf-8"
    ) as f:

        schema = json.load(f)

    merged = schema.copy()
    merged.update(blueprint)

    for key in schema:
        if (
            isinstance(schema[key], dict)
            and key in blueprint
            and isinstance(blueprint[key], dict)
        ):
            merged[key] = {**schema[key], **blueprint[key]}

    return merged


def _compile_ray(blueprint, output_path):

    from approch2.ray.ray_compiler import (
        RayCompiler
    )

    RayCompiler().compile_to_file(
        blueprint,
        str(output_path)
    )


def _compile_circuit(blueprint, output_path):

    from approch2.circuit.circuit_compiler import (
        CircuitCompiler
    )

    CircuitCompiler().compile_to_file(
        blueprint,
        str(output_path)
    )


def _compile_fbd(blueprint, output_path):

    from approch2.fbd.fbd_layout import (
        generate_layout
    )

    from approch2.fbd.fbd_renderer import (
        render_svg
    )

    layout = generate_layout(blueprint)

    svg = render_svg(layout)

    output_path.write_text(
        svg,
        encoding="utf-8"
    )


def _compile_magnetic(blueprint, output_path):

    from approch2.magnetic_field.mf_layout import (
        generate_layout
    )

    from approch2.magnetic_field.mf_field_engine import (
        generate_field
    )

    from approch2.magnetic_field.mf_renderer import (
        render_svg
    )

    layout = generate_layout(blueprint)

    generate_field(
        blueprint["object_type"]
    )

    svg = render_svg(layout)

    output_path.write_text(
        svg,
        encoding="utf-8"
    )


def _compile_semiconductor(blueprint, output_path):

    from approch2.semiconductor.semi_layout import (
        generate_layout
    )

    from approch2.semiconductor.semi_renderer import (
        render_svg
    )

    layout = generate_layout(blueprint)

    svg = render_svg(layout)

    output_path.write_text(
        svg,
        encoding="utf-8"
    )


def _compile_graph(blueprint, output_path):

    from approch2.graph.graph_renderer import (
        render_graph
    )

    render_graph(
        blueprint["object_type"],
        output_path
    )


COMPILERS = {
    "ray": _compile_ray,
    "circuit": _compile_circuit,
    "fbd": _compile_fbd,
    "magnetic": _compile_magnetic,
    "semiconductor": _compile_semiconductor,
    "graph": _compile_graph,
}


def load_schema(family):

    schema_file = (
        SCHEMA_DIR / family / f"{family}_schema.json"
    )

    if not schema_file.exists():
        return {}

    with open(
        schema_file,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def load_examples(family):

    examples_file = (
        SCHEMA_DIR / family / "examples.json"
    )

    if not examples_file.exists():
        return []

    with open(
        examples_file,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_json_output(data, directory, filename):

    path = directory / filename

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(data, f, indent=2)

    return path


def main():

    classifier = DiagramClassifier()

    generator = BlueprintGenerator()

    evaluator = BlueprintEvaluator()

    question = input("Question: ")

    classification = classifier.classify(question)

    if not classification.get("diagram_required"):

        print()
        print("No diagram required.")
        return

    family = classification.get("family", "").lower()

    if family not in COMPILERS:

        print()
        print(f"Unknown family: {family}")
        return

    schema = load_schema(family)

    examples = load_examples(family)

    # Step 1: Generate raw blueprint
    result = generator.generate_blueprint(
        question,
        family
    )

    raw_blueprint = result["blueprint"]

    qid = raw_blueprint.get(
        "question_id",
        f"{family}_output"
    )

    # Save raw blueprint
    save_json_output(
        raw_blueprint,
        RAW_BLUEPRINT_DIR,
        f"{qid}_raw.json"
    )

    # Step 2: Evaluate and enhance blueprint
    evaluation = evaluator.evaluate(
        question,
        family,
        schema,
        raw_blueprint,
        examples
    )

    enhanced_blueprint = evaluation.get(
        "enhanced_blueprint",
        raw_blueprint
    )

    # Save enhanced blueprint
    save_json_output(
        enhanced_blueprint,
        ENHANCED_BLUEPRINT_DIR,
        f"{qid}_enhanced.json"
    )

    # Save evaluation report
    save_json_output(
        evaluation,
        EVALUATION_REPORT_DIR,
        f"{qid}_evaluation.json"
    )

    # Step 3: Merge schema into enhanced blueprint
    merged_blueprint = _merge_schema(
        enhanced_blueprint,
        family
    )

    # Step 4: Compile enhanced blueprint
    output_path = COMPILED_SVG_DIR / f"{qid}.svg"

    COMPILERS[family](
        merged_blueprint,
        output_path
    )

    issues = evaluation.get("issues_found", [])
    improvements = evaluation.get("improvements", [])

    print()
    print("=" * 60)
    print("BLUEPRINT EVALUATION REPORT")
    print("=" * 60)

    print()
    print(f"Question : {question}")
    print(f"Family   : {family}")
    print(f"Issues   : {', '.join(issues) if issues else 'None'}")
    print(f"Changes  : {', '.join(improvements) if improvements else 'None'}")
    eval_status = "SUCCESS" if evaluation.get("valid", False) else "ISSUES FOUND"
    print(f"Evaluation Status : {eval_status}")
    print()
    print(f"Raw Blueprint      : {RAW_BLUEPRINT_DIR / f'{qid}_raw.json'}")
    print(f"Enhanced Blueprint : {ENHANCED_BLUEPRINT_DIR / f'{qid}_enhanced.json'}")
    print(f"Evaluation Report  : {EVALUATION_REPORT_DIR / f'{qid}_evaluation.json'}")
    print(f"Compiled SVG       : {output_path}")


if __name__ == "__main__":
    main()
