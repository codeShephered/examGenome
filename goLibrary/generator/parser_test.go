// File: generator/parser_test.go
package generator

import (
	"testing"
)

func TestSplitMCQs(t *testing.T) {
	raw := `Q1: A rectangle has a length of 12 cm and a width of 5 cm. What is its area?
A) 34 cm²   B) 60 cm²

Q2: A circle has a radius of 7 m. What is its area?
A) 49 m²   B) 153.9 m²`

	parts := SplitMCQs(raw)
	if len(parts) != 2 {
		t.Fatalf("expected 2 parts, got %d", len(parts))
	}
}

func TestSplitMCQs_Single(t *testing.T) {
	raw := "A triangle has sides 3, 4, 5. What is the perimeter?"
	parts := SplitMCQs(raw)
	if len(parts) != 1 {
		t.Fatalf("expected 1 part, got %d", len(parts))
	}
}

func TestClassifySchema(t *testing.T) {
	tests := []struct {
		text     string
		expected Schema
	}{
		{"A rectangle has a length of 12 cm and width 5 cm.", SchemaRectangle},
		{"A circle has a radius of 7 m.", SchemaCircle},
		{"A right triangle has base 9 m and height 12 m.", SchemaTriangle},
		{"A square has a side of 8 cm.", SchemaSquare},
		{"A pizza is divided into 8 equal slices.", SchemaFraction},
		{"What is 3 + 4?", SchemaGeneric},
	}
	for _, tt := range tests {
		got := classifySchema(tt.text)
		if got != tt.expected {
			t.Errorf("classifySchema(%q) = %q; want %q", tt.text, got, tt.expected)
		}
	}
}

func TestExtractDimensions(t *testing.T) {
	text := "A rectangle has a length of 15 cm and a width of 6 cm."
	dims := extractDimensions(text)
	if len(dims) < 2 {
		t.Fatalf("expected at least 2 dims, got %d", len(dims))
	}
	vals := map[float64]bool{15: false, 6: false}
	for _, d := range dims {
		vals[d.Value] = true
	}
	for v, found := range vals {
		if !found {
			t.Errorf("expected dimension %.0f not found", v)
		}
	}
}

func TestExtractFraction(t *testing.T) {
	text := "A pizza is divided into 8 equal slices. Mia eats 3 slices."
	total, eaten := extractFraction(text)
	if total != 8 {
		t.Errorf("total: got %d, want 8", total)
	}
	if eaten != 3 {
		t.Errorf("eaten: got %d, want 3", eaten)
	}
}

func TestExtractUnit(t *testing.T) {
	tests := []struct{ text, want string }{
		{"length of 12 cm", "cm"},
		{"radius of 5 m", "m"},
		{"side of 8 mm", "mm"},
		{"no unit here", "cm"}, // default
	}
	for _, tt := range tests {
		got := extractUnit(tt.text)
		if got != tt.want {
			t.Errorf("extractUnit(%q) = %q; want %q", tt.text, got, tt.want)
		}
	}
}

func TestParseMCQ_Rectangle(t *testing.T) {
	raw := `Q1: A rectangle has a length of 15 cm and a width of 6 cm. What is the perimeter?
A) 21 cm   B) 42 cm   C) 90 cm   D) 30 cm`

	p := ParseMCQ(1, raw)
	if p.Schema != SchemaRectangle {
		t.Errorf("schema: got %q, want %q", p.Schema, SchemaRectangle)
	}
	if len(p.Options) != 4 {
		t.Errorf("options: got %d, want 4", len(p.Options))
	}
	if p.Unit != "cm" {
		t.Errorf("unit: got %q, want cm", p.Unit)
	}
}

func TestParseMCQ_Fraction(t *testing.T) {
	raw := `Q1: A pizza is divided into 8 equal slices. Mia eats 3 slices. What fraction did she eat?
A) 3/8   B) 5/8   C) 1/4   D) 3/4`

	p := ParseMCQ(1, raw)
	if p.Schema != SchemaFraction {
		t.Errorf("schema: got %q, want fraction", p.Schema)
	}
	if p.TotalSlices != 8 {
		t.Errorf("TotalSlices: got %d, want 8", p.TotalSlices)
	}
	if p.EatenSlices != 3 {
		t.Errorf("EatenSlices: got %d, want 3", p.EatenSlices)
	}
}
