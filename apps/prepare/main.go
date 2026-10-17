package main

import (
	"bytes"
	"flag"
	"fmt"
	"image"
	_ "image/jpeg"
	"image/png"
	"os"
	"path/filepath"
	"runtime"
	"strings"

	"golang.org/x/image/draw"
	_ "golang.org/x/image/webp"
	"golang.org/x/sync/errgroup"
)

func main() {
	minPct := flag.Int("min", 1, "smallest scale, in percent of the original size")
	maxPct := flag.Int("max", 99, "largest scale, in percent of the original size")
	step := flag.Int("step", 1, "percent between consecutive scales")
	names := flag.String("methods", "", "comma-separated resampling methods, or all (default: interactive picker)\navailable: "+strings.Join(methodNames(), ", "))
	out := flag.String("out", "", "output directory (default: <image>_downscaled next to the input)")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "usage: downscale [flags] <image>\n\n")
		flag.PrintDefaults()
	}
	flag.Parse()

	if flag.NArg() != 1 {
		flag.Usage()
		os.Exit(2)
	}
	if err := run(flag.Arg(0), *out, *names, *minPct, *maxPct, *step); err != nil {
		fmt.Fprintln(os.Stderr, "downscale:", err)
		os.Exit(1)
	}
}

func run(src, out, names string, minPct, maxPct, step int) error {
	scales, err := percentages(minPct, maxPct, step)
	if err != nil {
		return err
	}
	selected, err := selectMethods(names)
	if err != nil {
		return err
	}
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	img, _, err := image.Decode(bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("decode %s: %w", src, err)
	}
	if out == "" {
		out = strings.TrimSuffix(src, filepath.Ext(src)) + "_downscaled"
	}
	if err := os.MkdirAll(out, 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(filepath.Join(out, "original"+filepath.Ext(src)), data, 0o644); err != nil {
		return err
	}

	var g errgroup.Group
	g.SetLimit(runtime.NumCPU())
	for _, m := range selected {
		dir := filepath.Join(out, m.name)
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
		for _, pct := range scales {
			g.Go(func() error {
				return save(filepath.Join(dir, fmt.Sprintf("%03d.png", pct)), resize(img, m.scaler, pct))
			})
		}
	}
	if err := g.Wait(); err != nil {
		return err
	}
	fmt.Printf("wrote %d images to %s\n", len(selected)*len(scales), out)
	return nil
}

func selectMethods(names string) ([]method, error) {
	switch names {
	case "":
		return pickMethods()
	case "all":
		return methods, nil
	}
	return lookupMethods(strings.Split(names, ","))
}

func percentages(minPct, maxPct, step int) ([]int, error) {
	if minPct < 1 || maxPct > 100 || minPct > maxPct {
		return nil, fmt.Errorf("need 1 <= min <= max <= 100, got min=%d max=%d", minPct, maxPct)
	}
	if step < 1 {
		return nil, fmt.Errorf("step must be positive, got %d", step)
	}
	var scales []int
	for p := minPct; p <= maxPct; p += step {
		scales = append(scales, p)
	}
	return scales, nil
}

func resize(src image.Image, s draw.Scaler, pct int) image.Image {
	b := src.Bounds()
	w := max(1, (b.Dx()*pct+50)/100)
	h := max(1, (b.Dy()*pct+50)/100)
	dst := image.NewRGBA(image.Rect(0, 0, w, h))
	s.Scale(dst, dst.Bounds(), src, b, draw.Src, nil)
	return dst
}

func save(path string, img image.Image) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	if err := png.Encode(f, img); err != nil {
		f.Close()
		return err
	}
	return f.Close()
}
