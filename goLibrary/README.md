# MCQ Math Image Generator — Go

Converts free-text Multiple Choice Questions into clean, kid-friendly SVG
diagrams. Zero external dependencies — pure Go standard library.

---

## Project layout

```
mcq_image_generator/
├── main.go                   ← Entry point; define MCQs here (or wire CLI/HTTP)
├── go.mod
└── generator/
    ├── parser.go             ← Stage 1 & 2: text parsing + schema classification
    ├── renderer.go           ← Stage 3: per-schema SVG rendering
    ├── batch.go              ← Stage 4: batch processor + HTML gallery writer
    └── parser_test.go        ← Unit tests
```

---

## Quick start

```bash
cd mcq_image_generator
go run .
# ✅  Generated 6 image(s) in ./output_images/
# 🌐  Preview gallery: ./output_images/gallery.html
```

Open `output_images/gallery.html` in any browser to see all diagrams.

---

## Architecture — four-stage pipeline

```
Raw MCQ text
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Stage 1 · SPLIT                                    │
│  SplitMCQs() — splits on Q1: / Q2: / ... markers   │
└──────────────────────────┬──────────────────────────┘
                           │  []string (one per MCQ)
                           ▼
┌─────────────────────────────────────────────────────┐
│  Stage 2 · PARSE  (parser.go)                       │
│  ParseMCQ() → ParsedMCQ struct                      │
│   • extractDimensions() — regex pulls all numbers   │
│   • extractUnit()        — cm / m / mm …            │
│   • extractOptions()     — A) B) C) D)              │
│   • classifySchema()     — rectangle / circle / …   │
│   • extractFraction()    — total & eaten slices     │
└──────────────────────────┬──────────────────────────┘
                           │  ParsedMCQ
                           ▼
┌─────────────────────────────────────────────────────┐
│  Stage 3 · RENDER  (renderer.go)                    │
│  RenderSVG() dispatches to per-schema function:     │
│   • renderRectangle()   • renderTriangle()          │
│   • renderCircle()      • renderFraction()          │
│   • renderGeneric()     (fallback)                  │
│  Output: inline SVG string, no external assets      │
└──────────────────────────┬──────────────────────────┘
                           │  SVG string
                           ▼
┌─────────────────────────────────────────────────────┐
│  Stage 4 · OUTPUT  (batch.go)                       │
│  ProcessBatch() writes q01_rectangle.svg …          │
│  WriteHTMLGallery() writes gallery.html             │
└─────────────────────────────────────────────────────┘
```

---

## Supported schemas

| Keyword(s) in MCQ          | Schema       | What is drawn                          |
|----------------------------|-------------|----------------------------------------|
| rectangle, length + width  | rectangle   | Labelled rect with dimension arrows    |
| square                     | square      | Equal-side rect with right-angle marks |
| triangle, triangular       | triangle    | Right or general triangle with labels  |
| circle, radius, diameter   | circle      | Circle with dashed radius/diameter     |
| fraction, equal slices     | fraction    | Pie chart, eaten vs. remaining         |
| (none matched)             | generic     | Placeholder with extracted measurements|

---

## Running tests

```bash
go test ./generator/...
```

---

## Extending the pipeline

### Adding a new schema (e.g. parallelogram)

1. Add `SchemaParallelogram Schema = "parallelogram"` in `parser.go`.
2. Add a keyword rule to `classifySchema()` in `parser.go`.
3. Add `renderParallelogram(p ParsedMCQ) string` in `renderer.go`.
4. Add a case to the `switch` in `RenderSVG()` in `renderer.go`.
5. Add a badge label + CSS class in `batch.go`.

### Exporting PNG (for LMS / PDF embed)

Use headless Chrome via `go-rod` or call `rsvg-convert`:

```go
cmd := exec.Command("rsvg-convert", "-w", "600", svgPath, "-o", pngPath)
```

Or install `github.com/go-rod/rod` and render the SVG string in a headless
browser tab to capture a screenshot as PNG.

### HTTP handler (for an API endpoint)

```go
http.HandleFunc("/generate", func(w http.ResponseWriter, r *http.Request) {
    body, _ := io.ReadAll(r.Body)
    results, err := generator.ProcessBatch(generator.SplitMCQs(string(body)), tmpDir)
    if err != nil { http.Error(w, err.Error(), 500); return }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(results)
})
```

### AI fallback for complex MCQs

For ambiguous MCQs where the regex classifier returns `SchemaGeneric`, route
to the Claude API with a structured prompt:

```go
// Pseudocode
prompt := fmt.Sprintf(`Extract the math shape and all dimensions from:
"%s"
Return JSON: {"schema":"rectangle","dimensions":[{"value":12,"unit":"cm"}]}`, mcq)
// Call Anthropic API → parse JSON → override p.Schema and p.Dimensions
```

---

## Design principles

- **Question only, never the answer.** SVG labels show dimensions from the
  question stem; MCQ options are listed separately as text, not drawn.
- **Kid-readable.** Font size ≥ 14 px, bold weights, high-contrast fills,
  named labels ("base", "height", "radius").
- **No external dependencies.** Pure `encoding/xml`, `math`, `regexp`,
  `strings`. No CGo, no OS-specific code.
- **Proportional scaling.** Shapes are scaled to a `maxPx` budget so a
  "1 cm rectangle" and a "200 m rectangle" both render readably.
