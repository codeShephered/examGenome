// Package generator provides the full MCQ → Math Image pipeline.
// File: generator/parser.go  — MCQ text parsing & classification
package generator

import (
	"regexp"
	"strconv"
	"strings"
)

// Schema is the geometric/visual type we map each MCQ to.
type Schema string

const (
	SchemaRectangle Schema = "rectangle"
	SchemaSquare    Schema = "square"
	SchemaTriangle  Schema = "triangle"
	SchemaCircle    Schema = "circle"
	SchemaFraction  Schema = "fraction"
	SchemaNumberLine Schema = "number-line"
	SchemaGrid      Schema = "grid"
	SchemaGeneric   Schema = "generic"
)

// Dimension holds a parsed numeric value and its unit.
type Dimension struct {
	Value float64
	Unit  string
}

// Option holds a single MCQ answer option (letter + text).
type Option struct {
	Letter string
	Text   string
}

// ParsedMCQ is the structured representation of one MCQ.
type ParsedMCQ struct {
	Index        int
	RawText      string
	QuestionText string
	Schema       Schema
	Dimensions   []Dimension
	Unit         string
	Options      []Option
	// Fraction-specific
	TotalSlices int
	EatenSlices int
}

// ── Compiled regexps (compiled once at startup) ───────────────────────────

var (
	reDimension = regexp.MustCompile(
		`(\d+(?:\.\d+)?)\s*` +
			`(cm|m|mm|km|ft|in|inches?|meters?|centimeters?|feet)?` +
			`(?:\s*(?:by|x|×)\s*(\d+(?:\.\d+)?)\s*(cm|m|mm|km|ft|in)?)?`,
	)
	reOptions    = regexp.MustCompile(`(?m)^([A-D])[).]\s*(.+)$`)
	reQText      = regexp.MustCompile(`(?i)Q\d+[.:]\s*([\s\S]+?)(?:\n[A-D][).])`)
	reTotalSlice = regexp.MustCompile(`(?i)(\d+)\s*equal\s*(?:slices|parts|pieces|sections)`)
	reEaten      = regexp.MustCompile(`(?i)(?:eats?|ate|takes?|shaded?|colou?rs?)\s*(\d+)`)
	reSplit      = regexp.MustCompile(`(?m)^(Q\d+[.:])\s`)
	reUnit       = regexp.MustCompile(`\b(cm|m|mm|km|ft|in|inches|meters|centimeters|feet)\b`)
)

// SplitMCQs splits a multi-MCQ string on "Q1: / Q2: / ..." markers.
// If no markers are found the whole string is treated as one MCQ.
func SplitMCQs(raw string) []string {
	raw = strings.TrimSpace(raw)
	indices := reSplit.FindAllStringIndex(raw, -1)
	if len(indices) == 0 {
		return []string{raw}
	}
	parts := make([]string, 0, len(indices))
	for i, loc := range indices {
		start := loc[0]
		end := len(raw)
		if i+1 < len(indices) {
			end = indices[i+1][0]
		}
		part := strings.TrimSpace(raw[start:end])
		if part != "" {
			parts = append(parts, part)
		}
	}
	return parts
}

// ParseMCQ analyses a single MCQ string and returns a ParsedMCQ.
func ParseMCQ(index int, raw string) ParsedMCQ {
	p := ParsedMCQ{
		Index:   index,
		RawText: raw,
	}
	p.QuestionText = extractQuestion(raw)
	p.Dimensions = extractDimensions(raw)
	p.Unit = extractUnit(raw)
	p.Options = extractOptions(raw)
	p.Schema = classifySchema(raw)

	if p.Schema == SchemaFraction {
		p.TotalSlices, p.EatenSlices = extractFraction(raw)
	}
	return p
}

// ── Internal helpers ──────────────────────────────────────────────────────

func extractQuestion(text string) string {
	if m := reQText.FindStringSubmatch(text); len(m) > 1 {
		return strings.TrimSpace(strings.ReplaceAll(m[1], "\n", " "))
	}
	// Fallback: first non-empty line, stripped of "Q1:" prefix.
	for _, line := range strings.Split(text, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		line = regexp.MustCompile(`(?i)^Q\d+[.:]?\s*`).ReplaceAllString(line, "")
		return strings.TrimSpace(line)
	}
	return text
}

func extractDimensions(text string) []Dimension {
	var dims []Dimension
	seen := map[string]bool{}

	matches := reDimension.FindAllStringSubmatch(text, -1)
	for _, m := range matches {
		if m[1] == "" {
			continue
		}
		v, err := strconv.ParseFloat(m[1], 64)
		if err != nil || v == 0 {
			continue
		}
		u := normaliseUnit(m[2])
		key := m[1] + u
		if !seen[key] {
			seen[key] = true
			dims = append(dims, Dimension{Value: v, Unit: u})
		}
		// Second value in "12 by 5" pattern
		if m[3] != "" {
			v2, err := strconv.ParseFloat(m[3], 64)
			if err == nil && v2 != 0 {
				u2 := normaliseUnit(m[4])
				if u2 == "" {
					u2 = u
				}
				key2 := m[3] + u2
				if !seen[key2] {
					seen[key2] = true
					dims = append(dims, Dimension{Value: v2, Unit: u2})
				}
			}
		}
	}
	return dims
}

func extractUnit(text string) string {
	if m := reUnit.FindStringSubmatch(text); len(m) > 1 {
		return normaliseUnit(m[1])
	}
	return "cm"
}

func normaliseUnit(u string) string {
	switch strings.ToLower(u) {
	case "meters", "meter":
		return "m"
	case "centimeters", "centimeter":
		return "cm"
	case "inches", "inch":
		return "in"
	case "feet", "foot":
		return "ft"
	default:
		return strings.ToLower(u)
	}
}

func extractOptions(text string) []Option {
	var opts []Option
	for _, m := range reOptions.FindAllStringSubmatch(text, -1) {
		if len(m) >= 3 {
			opts = append(opts, Option{Letter: m[1], Text: strings.TrimSpace(m[2])})
		}
	}
	return opts
}

func classifySchema(text string) Schema {
	t := strings.ToLower(text)
	switch {
	case strings.Contains(t, "circle") ||
		strings.Contains(t, "radius") ||
		strings.Contains(t, "diameter") ||
		strings.Contains(t, "circumference"):
		return SchemaCircle

	case strings.Contains(t, "triangle") ||
		strings.Contains(t, "triangular"):
		return SchemaTriangle

	case strings.Contains(t, "square"):
		return SchemaSquare

	case strings.Contains(t, "rectangle") ||
		strings.Contains(t, "rectangular") ||
		regexp.MustCompile(`length.{1,25}width|width.{1,25}length`).MatchString(t):
		return SchemaRectangle

	case strings.Contains(t, "fraction") ||
		strings.Contains(t, "equal slices") ||
		strings.Contains(t, "equal parts") ||
		strings.Contains(t, "divided"):
		return SchemaFraction

	case strings.Contains(t, "number line"):
		return SchemaNumberLine

	case strings.Contains(t, "grid") ||
		strings.Contains(t, "array") ||
		regexp.MustCompile(`\d+\s*rows?\s+\d+\s*col`).MatchString(t):
		return SchemaGrid

	default:
		return SchemaGeneric
	}
}

func extractFraction(text string) (total, eaten int) {
	total, eaten = 8, 3 // sensible defaults
	if m := reTotalSlice.FindStringSubmatch(text); len(m) > 1 {
		if v, err := strconv.Atoi(m[1]); err == nil {
			total = v
		}
	}
	if m := reEaten.FindStringSubmatch(text); len(m) > 1 {
		if v, err := strconv.Atoi(m[1]); err == nil {
			eaten = v
		}
	}
	return
}
