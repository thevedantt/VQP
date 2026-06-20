from flux_service import FluxService



prompt = """
Create a clean CBSE Physics textbook ray diagram of an astronomical telescope in normal adjustment.

Style:
- Black and white scientific textbook illustration.
- Thin precise vector lines.
- White background.
- No shading, no colors, no artistic effects.
- High-resolution educational diagram.
- Engineering drawing style.
- All text in serif textbook font.

Layout:
- Horizontal principal axis through the center of the page.
- Convex objective lens on the left, vertically oriented.
- Convex eyepiece lens on the right, vertically oriented.
- Objective lens labeled: "Objective (fo)".
- Eyepiece lens labeled: "Eyepiece (fe)".

Object rays:
- Three parallel rays coming from a distant object on the far left.
- Label on left:
  "Parallel rays
   from a distant
   object"

Ray tracing:
- After passing through the objective lens, the rays converge to a common focal point located between the two lenses.
- The common focal point lies on the principal axis.
- Label this point:
  "Fo (= Fe')"

Lens spacing:
- Distance from objective lens to common focal point labeled "fo".
- Distance from common focal point to eyepiece lens labeled "fe".
- Show dimension arrows beneath the principal axis.

Eyepiece action:
- Rays emerging from the eyepiece become parallel again.
- Three parallel rays exit toward the right side.

Eye:
- Draw a simple eye symbol on the far right.
- Label:
  "Parallel rays
   (to eye)"

Additional labels:
- Mark focal point of eyepiece on the principal axis to the right of the eyepiece and label it "Fe".

Formula section:
- Centered below the diagram write:

  Magnifying power,
  M = angle subtended by final image at eye
      --------------------------------------
      angle subtended by object at eye

  M = -fo / fe

Composition:
- Objective lens at left third.
- Eyepiece lens at right third.
- Converging point exactly between lenses.
- All labels clear and readable.
- Match the appearance of a CBSE/NCERT Physics textbook optical instrument diagram.

Aspect ratio: wide landscape.
"""
flux = FluxService()

result = flux.generate_image(prompt)

print(result)
