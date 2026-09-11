// File: generator/batch.go  — batch processing + file output + HTML gallery
package generator

import (
	"fmt"
	"html"
	"os"
	"path/filepath"
	"strings"
)

// Result holds the output of processing one MCQ.
type Result struct {
	Index     int
	Schema    Schema
	SVGContent string
	FilePath  string
	MCQ       ParsedMCQ
}

// ProcessBatch parses, classifies, renders, and saves SVG files for all MCQs.
// rawMCQs is a slice of individual MCQ strings (use SplitMCQs to produce it).
// outDir is the directory where .svg files will be written.
func ProcessBatch(rawMCQs []string, outDir string) ([]Result, error) {
	results := make([]Result, 0, len(rawMCQs))

	for i, raw := range rawMCQs {
		// 1. Parse
		p := ParseMCQ(i+1, raw)

		// 2. Render SVG
		svgContent := RenderSVG(p)

		// 3. Write to file
		fname := fmt.Sprintf("q%02d_%s.svg", i+1, string(p.Schema))
		fpath := filepath.Join(outDir, fname)
		if err := os.WriteFile(fpath, []byte(svgContent), 0644); err != nil {
			return results, fmt.Errorf("writing SVG for Q%d: %w", i+1, err)
		}

		results = append(results, Result{
			Index:      i + 1,
			Schema:     p.Schema,
			SVGContent: svgContent,
			FilePath:   fpath,
			MCQ:        p,
		})
	}
	return results, nil
}

// ProcessRaw is a convenience wrapper: it splits a multi-MCQ string and
// then calls ProcessBatch. Useful for HTTP handlers or CLI pipes.
func ProcessRaw(raw string, outDir string) ([]Result, error) {
	parts := SplitMCQs(raw)
	return ProcessBatch(parts, outDir)
}

// WriteHTMLGallery generates a self-contained HTML page that embeds all
// generated SVGs as an inline preview gallery.
func WriteHTMLGallery(results []Result, outPath string) error {
	var body strings.Builder

	for _, r := range results {
		opts := optionsHTML(r.MCQ.Options)
		badge := badgeHTML(r.Schema)

		body.WriteString(fmt.Sprintf(`
<div class="card">
  <div class="card-header">
    <span class="q-num">Question %d</span>
    %s
  </div>
  <div class="card-body">
    <p class="q-text">%s</p>
    <div class="img-wrap">
      %s
    </div>
    %s
    <p class="hint">↑ Image shows the question setup only — not the answer.</p>
  </div>
</div>
`, r.Index, badge, html.EscapeString(r.MCQ.QuestionText), r.SVGContent, opts))
	}

	page := fmt.Sprintf(`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MCQ Math Image Gallery</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Nunito',sans-serif;background:#F8FAFC;color:#1E293B;padding:32px 16px}
h1{font-size:26px;font-weight:800;text-align:center;margin-bottom:6px}
.subtitle{text-align:center;color:#64748B;font-size:14px;margin-bottom:32px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px;max-width:1100px;margin:0 auto}
.card{background:#fff;border-radius:14px;border:1px solid #E2E8F0;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.card-header{padding:12px 16px;background:#F1F5F9;border-bottom:1px solid #E2E8F0;display:flex;justify-content:space-between;align-items:center}
.q-num{font-size:13px;font-weight:800;color:#1E293B}
.badge{padding:3px 9px;border-radius:5px;font-size:11px;font-weight:800}
.badge-rectangle{background:#DBEAFE;color:#1D4ED8}
.badge-square{background:#EDE9FE;color:#5B21B6}
.badge-triangle{background:#DCFCE7;color:#166534}
.badge-circle{background:#FEF3C7;color:#92400E}
.badge-fraction{background:#FCE7F3;color:#9D174D}
.badge-generic,.badge-number-line,.badge-grid{background:#F1F5F9;color:#475569}
.card-body{padding:16px}
.q-text{font-size:14px;font-weight:700;color:#1E293B;line-height:1.6;margin-bottom:12px}
.img-wrap{background:#F8FAFC;border-radius:10px;padding:16px;display:flex;justify-content:center;margin-bottom:12px}
.options{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px}
.option{padding:8px 12px;border:1px solid #E2E8F0;border-radius:7px;font-size:13px;color:#64748B;background:#F8FAFC}
.option strong{color:#1E293B;margin-right:6px}
.hint{font-size:11px;color:#94A3B8;border-left:3px solid #3B82F6;padding-left:8px}
</style>
</head>
<body>
<h1>Math Image Gallery</h1>
<p class="subtitle">Auto-generated diagrams from MCQs — question setup only, no answers revealed</p>
<div class="grid">
%s
</div>
</body>
</html>`, body.String())

	return os.WriteFile(outPath, []byte(page), 0644)
}

// ── HTML helpers ──────────────────────────────────────────────────────────

func optionsHTML(opts []Option) string {
	if len(opts) < 2 {
		return ""
	}
	var sb strings.Builder
	sb.WriteString(`<div class="options">`)
	for _, o := range opts {
		sb.WriteString(fmt.Sprintf(
			`<div class="option"><strong>%s)</strong>%s</div>`,
			html.EscapeString(o.Letter),
			html.EscapeString(o.Text),
		))
	}
	sb.WriteString(`</div>`)
	return sb.String()
}

func badgeHTML(s Schema) string {
	labels := map[Schema]string{
		SchemaRectangle:  "Rectangle",
		SchemaSquare:     "Square",
		SchemaTriangle:   "Triangle",
		SchemaCircle:     "Circle",
		SchemaFraction:   "Fraction",
		SchemaNumberLine: "Number Line",
		SchemaGrid:       "Grid",
		SchemaGeneric:    "Shape",
	}
	lbl, ok := labels[s]
	if !ok {
		lbl = "Shape"
	}
	return fmt.Sprintf(`<span class="badge badge-%s">%s</span>`, string(s), lbl)
}
