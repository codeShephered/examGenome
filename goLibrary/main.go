package main

import (
	"fmt"
	"log"
	"os"

	"mcq_image_generator/generator"
)

func main() {
	// ── Sample MCQs (replace with file input or API feed in production) ──────
	mcqs := []string{
		`Q1: A rectangle has a length of 15 cm and a width of 6 cm. What is the perimeter?
A) 21 cm   B) 90 cm   C) 42 cm   D) 30 cm`,

		`Q2: A right triangle has a base of 9 m and a height of 12 m. What is its area?
A) 108 m²   B) 54 m²   C) 42 m²   D) 216 m²`,

		`Q3: A circle has a radius of 5 m. What is the area? (Use π ≈ 3.14)
A) 15.7 m²   B) 31.4 m²   C) 78.5 m²   D) 25 m²`,

		`Q4: A square has a side of 8 cm. What is the area?
A) 32 cm²   B) 64 cm²   C) 16 cm²   D) 128 cm²`,

		`Q5: A pizza is divided into 8 equal slices. Mia eats 3 slices. What fraction of the pizza did she eat?
A) 3/4   B) 5/8   C) 3/8   D) 1/3`,

		`Q6: A triangle has sides of 7 cm, 7 cm, and 10 cm. What is its perimeter?
A) 24 cm   B) 17 cm   C) 49 cm   D) 70 cm`,
	}

	outDir := "output_images"
	if err := os.MkdirAll(outDir, 0755); err != nil {
		log.Fatalf("failed to create output dir: %v", err)
	}

	results, err := generator.ProcessBatch(mcqs, outDir)
	if err != nil {
		log.Fatalf("batch processing failed: %v", err)
	}

	fmt.Printf("\n✅  Generated %d image(s) in ./%s/\n\n", len(results), outDir)
	for _, r := range results {
		fmt.Printf("  %-10s  →  %s\n", r.Schema, r.FilePath)
	}

	// Also write a self-contained HTML gallery for easy preview
	if err := generator.WriteHTMLGallery(results, outDir+"/gallery.html"); err != nil {
		log.Fatalf("failed to write gallery: %v", err)
	}
	fmt.Printf("\n🌐  Preview gallery: ./%s/gallery.html\n\n", outDir)
}
