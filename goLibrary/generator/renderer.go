// File: generator/renderer.go  — per-schema SVG renderers
package generator

import (
	"fmt"
	"math"
	"strings"
)

// arrowDefs is the shared SVG <defs> block included in every diagram.
const arrowDefs = `<defs>
  <marker id="aw" viewBox="0 0 10 10" refX="5" refY="5"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M2 2L8 5L2 8" fill="none" stroke="%s"
          stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
</defs>`

// RenderSVG dispatches to the right renderer based on schema.
func RenderSVG(p ParsedMCQ) string {
	switch p.Schema {
	case SchemaRectangle:
		return renderRectangle(p, false)
	case SchemaSquare:
		return renderRectangle(p, true)
	case SchemaTriangle:
		return renderTriangle(p)
	case SchemaCircle:
		return renderCircle(p)
	case SchemaFraction:
		return renderFraction(p)
	default:
		return renderGeneric(p)
	}
}

// ── Rectangle / Square ────────────────────────────────────────────────────

func renderRectangle(p ParsedMCQ, isSquare bool) string {
	col := "#2563EB"
	fill := "#DBEAFE"
	if isSquare {
		col = "#7C3AED"
		fill = "#EDE9FE"
	}

	// Pull first two unique dimension values.
	w, h, unit := rectDims(p, isSquare)

	const maxPx = 160.0
	scale := maxPx / math.Max(w, h)
	rw := math.Round(w * scale)
	rh := math.Round(h * scale)

	// Canvas sizing: leave room for arrows and labels on right + bottom.
	canvasW := rw + 160.0
	canvasH := rh + 160.0
	ox, oy := 60.0, 50.0

	defs := fmt.Sprintf(arrowDefs, col)
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf(
		`<svg viewBox="0 0 %.0f %.0f" width="340" xmlns="http://www.w3.org/2000/svg">
%s
`,
		canvasW, canvasH, defs,
	))

	// Shape
	sb.WriteString(fmt.Sprintf(
		`  <rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" rx="6"
        fill="%s" stroke="%s" stroke-width="2.5"/>
`,
		ox, oy, rw, rh, fill, col,
	))

	// Square right-angle marks
	if isSquare {
		sb.WriteString(fmt.Sprintf(
			`  <rect x="%.0f" y="%.0f" width="12" height="12" fill="none" stroke="%s" stroke-width="1.5"/>
  <rect x="%.0f" y="%.0f" width="12" height="12" fill="none" stroke="%s" stroke-width="1.5"/>
`,
			ox, oy+rh-12, col,
			ox+rw-12, oy, col,
		))
	}

	// Width arrow (bottom)
	ay := oy + rh + 30
	sb.WriteString(fmt.Sprintf(
		`  <line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="%s" stroke-width="2"
         marker-start="url(#aw)" marker-end="url(#aw)"/>
  <text x="%.0f" y="%.0f" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="16" font-weight="800" fill="%s">%s</text>
`,
		ox, ay, ox+rw, ay, col,
		ox+rw/2, ay+22, col,
		fmtDim(w, unit),
	))

	// Height arrow (right side)
	ax := ox + rw + 32
	label := "height"
	if isSquare {
		label = "side"
	}
	_ = label
	sb.WriteString(fmt.Sprintf(
		`  <line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="%s" stroke-width="2"
         marker-start="url(#aw)" marker-end="url(#aw)"/>
  <text x="%.0f" y="%.0f" text-anchor="start"
        font-family="Nunito,Arial,sans-serif" font-size="16" font-weight="800" fill="%s">%s</text>
`,
		ax, oy, ax, oy+rh, col,
		ax+12, oy+rh/2+6, col,
		fmtDim(h, unit),
	))

	if isSquare {
		sb.WriteString(fmt.Sprintf(
			`  <text x="%.0f" y="%.0f" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="13" font-weight="700" fill="%s">Square</text>
`,
			ox+rw/2, oy+rh/2+6, "#5B21B6",
		))
	} else {
		sb.WriteString(fmt.Sprintf(
			`  <text x="%.0f" y="%.0f" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="12" fill="%s">length</text>
  <text x="%.0f" y="%.0f" text-anchor="start"
        font-family="Nunito,Arial,sans-serif" font-size="12" fill="%s">width</text>
`,
			ox+rw/2, ay+38, "#1D4ED8",
			ax+12, oy+rh/2+22, "#1D4ED8",
		))
	}

	sb.WriteString("</svg>")
	return sb.String()
}

func rectDims(p ParsedMCQ, isSquare bool) (w, h float64, unit string) {
	unit = p.Unit
	dims := p.Dimensions

	if len(dims) >= 2 {
		w, h = dims[0].Value, dims[1].Value
		if dims[0].Unit != "" {
			unit = dims[0].Unit
		}
	} else if len(dims) == 1 {
		w = dims[0].Value
		if isSquare {
			h = w
		} else {
			h = w / 2
		}
		if dims[0].Unit != "" {
			unit = dims[0].Unit
		}
	} else {
		w, h = 10, 6
	}
	return
}

// ── Triangle ──────────────────────────────────────────────────────────────

func renderTriangle(p ParsedMCQ) string {
	col := "#16A34A"
	fill := "#DCFCE7"

	isRight := isRightTriangle(p.RawText)
	a, b, c, unit := triDims(p)

	scale := 130.0 / math.Max(a, b)
	bPx := math.Round(a * scale)
	hPx := math.Round(b * scale)

	canvasW := bPx + 200
	canvasH := hPx + 180
	ox, oy := 80.0, 50.0

	var pts string
	if isRight {
		pts = fmt.Sprintf("%.0f,%.0f %.0f,%.0f %.0f,%.0f",
			ox, oy+hPx, ox+bPx, oy+hPx, ox, oy)
	} else {
		pts = fmt.Sprintf("%.0f,%.0f %.0f,%.0f %.0f,%.0f",
			ox+bPx/2, oy, ox, oy+hPx, ox+bPx, oy+hPx)
	}

	defs := fmt.Sprintf(arrowDefs, col)
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf(
		`<svg viewBox="0 0 %.0f %.0f" width="340" xmlns="http://www.w3.org/2000/svg">
%s
  <polygon points="%s" fill="%s" stroke="%s" stroke-width="2.5" stroke-linejoin="round"/>
`,
		canvasW, canvasH, defs, pts, fill, col,
	))

	// Right-angle mark
	if isRight {
		sb.WriteString(fmt.Sprintf(
			`  <rect x="%.0f" y="%.0f" width="14" height="14" fill="none" stroke="%s" stroke-width="1.5"/>
`,
			ox, oy+hPx-14, col,
		))
	}

	// Base label
	baseLabelY := oy + hPx + 28
	sb.WriteString(fmt.Sprintf(
		`  <text x="%.0f" y="%.0f" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="15" font-weight="800" fill="%s">%s</text>
`,
		ox+bPx/2, baseLabelY, col, fmtDim(a, unit),
	))

	// Height / second side label
	if isRight {
		sb.WriteString(fmt.Sprintf(
			`  <text x="%.0f" y="%.0f" text-anchor="end"
        font-family="Nunito,Arial,sans-serif" font-size="15" font-weight="800" fill="%s">%s</text>
`,
			ox-12, oy+hPx/2+6, col, fmtDim(b, unit),
		))
	} else {
		sb.WriteString(fmt.Sprintf(
			`  <text x="%.0f" y="%.0f" text-anchor="start"
        font-family="Nunito,Arial,sans-serif" font-size="15" font-weight="800" fill="%s">%s</text>
`,
			ox+bPx+12, oy+hPx/2, col, fmtDim(b, unit),
		))
	}

	// Third side for non-right triangles
	if !isRight && c > 0 {
		sb.WriteString(fmt.Sprintf(
			`  <text x="%.0f" y="%.0f" text-anchor="end"
        font-family="Nunito,Arial,sans-serif" font-size="15" font-weight="800" fill="%s">%s</text>
`,
			ox-12, oy+hPx/2, col, fmtDim(c, unit),
		))
	}

	// Sub-labels
	if isRight {
		sb.WriteString(fmt.Sprintf(
			`  <text x="%.0f" y="%.0f" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="12" fill="#166534">base</text>
  <text x="%.0f" y="%.0f" text-anchor="end"
        font-family="Nunito,Arial,sans-serif" font-size="12" fill="#166534">height</text>
`,
			ox+bPx/2, baseLabelY+18,
			ox-12, oy+hPx/2+22,
		))
	}

	sb.WriteString("</svg>")
	return sb.String()
}

func triDims(p ParsedMCQ) (a, b, c float64, unit string) {
	unit = p.Unit
	dims := p.Dimensions
	switch len(dims) {
	case 0:
		a, b = 9, 12
	case 1:
		a, b = dims[0].Value, dims[0].Value
	case 2:
		a, b = dims[0].Value, dims[1].Value
	default:
		a, b, c = dims[0].Value, dims[1].Value, dims[2].Value
	}
	if len(dims) > 0 && dims[0].Unit != "" {
		unit = dims[0].Unit
	}
	return
}

func isRightTriangle(text string) bool {
	t := strings.ToLower(text)
	return strings.Contains(t, "right triangle") ||
		strings.Contains(t, "right-angle") ||
		strings.Contains(t, "right angle") ||
		strings.Contains(t, "90") ||
		strings.Contains(t, "height") && strings.Contains(t, "base")
}

// ── Circle ────────────────────────────────────────────────────────────────

func renderCircle(p ParsedMCQ) string {
	col := "#D97706"
	fill := "#FEF3C7"

	isDiam := isDiameter(p.RawText)
	r, unit := circDim(p)
	radius := r
	if isDiam {
		radius = r / 2
	}

	rPx := math.Min(110, math.Max(60, radius*14))
	cx, cy := 150.0, 130.0

	canvasH := cy + rPx + 90

	defs := fmt.Sprintf(arrowDefs, col)
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf(
		`<svg viewBox="0 0 320 %.0f" width="300" xmlns="http://www.w3.org/2000/svg">
%s
  <circle cx="%.0f" cy="%.0f" r="%.0f" fill="%s" stroke="%s" stroke-width="2.5"/>
  <circle cx="%.0f" cy="%.0f" r="5" fill="%s"/>
`,
		canvasH, defs,
		cx, cy, rPx, fill, col,
		cx, cy, col,
	))

	if isDiam {
		sb.WriteString(fmt.Sprintf(
			`  <line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f"
         stroke="%s" stroke-width="2" stroke-dasharray="5 4"/>
  <text x="%.0f" y="%.0f" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="14" font-weight="800" fill="%s">diameter = %s</text>
`,
			cx-rPx, cy, cx+rPx, cy, col,
			cx, cy-14, col, fmtDim(r, unit),
		))
	} else {
		sb.WriteString(fmt.Sprintf(
			`  <line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f"
         stroke="%s" stroke-width="2" stroke-dasharray="5 4"/>
  <text x="%.0f" y="%.0f" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="14" font-weight="800" fill="%s">r = %s</text>
`,
			cx, cy, cx+rPx, cy, col,
			cx+rPx/2, cy-14, col, fmtDim(radius, unit),
		))
	}

	lbl := "radius"
	if isDiam {
		lbl = "diameter"
	}
	sb.WriteString(fmt.Sprintf(
		`  <text x="%.0f" y="%.0f" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="12" fill="#92400E" font-weight="600">%s = %s</text>
`,
		cx, cy+rPx+34, lbl, fmtDim(r, unit),
	))

	sb.WriteString("</svg>")
	return sb.String()
}

func isDiameter(text string) bool {
	return strings.Contains(strings.ToLower(text), "diameter")
}

func circDim(p ParsedMCQ) (float64, string) {
	if len(p.Dimensions) > 0 {
		d := p.Dimensions[0]
		u := d.Unit
		if u == "" {
			u = p.Unit
		}
		return d.Value, u
	}
	return 5, p.Unit
}

// ── Fraction (pie chart) ──────────────────────────────────────────────────

func renderFraction(p ParsedMCQ) string {
	total := p.TotalSlices
	eaten := p.EatenSlices
	if total < 2 {
		total = 8
	}
	if eaten < 0 || eaten > total {
		eaten = total / 2
	}

	cx, cy, r := 130.0, 120.0, 90.0
	canvasW := cx + r + 140
	canvasH := cy + r + 80

	var sb strings.Builder
	sb.WriteString(fmt.Sprintf(
		`<svg viewBox="0 0 %.0f %.0f" width="340" xmlns="http://www.w3.org/2000/svg">
`,
		canvasW, canvasH,
	))

	sliceAngle := 2 * math.Pi / float64(total)
	startAngle := -math.Pi / 2 // 12 o'clock

	for i := 0; i < total; i++ {
		sa := startAngle + float64(i)*sliceAngle
		ea := sa + sliceAngle

		x1 := cx + r*math.Cos(sa)
		y1 := cy + r*math.Sin(sa)
		x2 := cx + r*math.Cos(ea)
		y2 := cy + r*math.Sin(ea)

		fillColor := "#FEE2E2"
		strokeColor := "#F87171"
		if i < eaten {
			fillColor = "#DC2626"
			strokeColor = "#991B1B"
		}
		_ = strokeColor

		largeArc := 0
		if sliceAngle > math.Pi {
			largeArc = 1
		}

		sb.WriteString(fmt.Sprintf(
			`  <path d="M%.2f,%.2f L%.2f,%.2f A%.2f,%.2f,0,%d,1,%.2f,%.2f Z"
        fill="%s" stroke="#fff" stroke-width="2"/>
`,
			cx, cy, x1, y1, r, r, largeArc, x2, y2, fillColor,
		))
	}

	// Outer ring
	sb.WriteString(fmt.Sprintf(
		`  <circle cx="%.0f" cy="%.0f" r="%.0f" fill="none" stroke="#991B1B" stroke-width="2"/>
`,
		cx, cy, r,
	))

	// Caption
	sb.WriteString(fmt.Sprintf(
		`  <text x="%.0f" y="%.0f" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="16" font-weight="800" fill="#991B1B">%d out of %d slices</text>
`,
		cx, cy+r+34, eaten, total,
	))

	// Legend
	lx := cx + r + 20
	sb.WriteString(fmt.Sprintf(
		`  <rect x="%.0f" y="30" width="16" height="16" rx="3" fill="#DC2626"/>
  <text x="%.0f" y="43" font-family="Nunito,Arial,sans-serif" font-size="12" font-weight="700" fill="#374151">eaten (%d)</text>
  <rect x="%.0f" y="56" width="16" height="16" rx="3" fill="#FEE2E2" stroke="#F87171" stroke-width="1"/>
  <text x="%.0f" y="69" font-family="Nunito,Arial,sans-serif" font-size="12" font-weight="700" fill="#374151">remaining (%d)</text>
`,
		lx, lx+22, eaten,
		lx, lx+22, total-eaten,
	))

	sb.WriteString("</svg>")
	return sb.String()
}

// ── Generic fallback ──────────────────────────────────────────────────────

func renderGeneric(p ParsedMCQ) string {
	lines := []string{"Shape detected from question."}
	if len(p.Dimensions) > 0 {
		var dStrs []string
		for _, d := range p.Dimensions[:min(4, len(p.Dimensions))] {
			dStrs = append(dStrs, fmtDim(d.Value, d.Unit))
		}
		lines = append(lines, "Measurements: "+strings.Join(dStrs, ", "))
	} else {
		lines = append(lines, "No measurements found.")
	}
	lines = append(lines, "Add shape keywords for", "a full diagram.")

	var sb strings.Builder
	sb.WriteString(`<svg viewBox="0 0 300 170" width="280" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="280" height="150" rx="10"
        fill="#F3F4F6" stroke="#9CA3AF" stroke-width="1.5" stroke-dasharray="5 3"/>
  <text x="150" y="48" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="22">📐</text>
`)
	for i, line := range lines {
		sb.WriteString(fmt.Sprintf(
			`  <text x="150" y="%d" text-anchor="middle"
        font-family="Nunito,Arial,sans-serif" font-size="12" fill="#6B7280">%s</text>
`,
			72+i*20, line,
		))
	}
	sb.WriteString("</svg>")
	return sb.String()
}

// ── Utility helpers ───────────────────────────────────────────────────────

func fmtDim(v float64, unit string) string {
	if v == math.Trunc(v) {
		return fmt.Sprintf("%.0f %s", v, unit)
	}
	return fmt.Sprintf("%.1f %s", v, unit)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
