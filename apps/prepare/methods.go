package main

import (
	"fmt"
	"math"
	"slices"
	"strings"

	"golang.org/x/image/draw"
)

type method struct {
	name   string
	scaler draw.Scaler
}

var methods = []method{
	{"nearest", draw.NearestNeighbor},
	{"fast-bilinear", draw.ApproxBiLinear},
	{"bilinear", draw.BiLinear},
	{"bicubic", draw.CatmullRom},
	{"mitchell", mitchell},
	{"lanczos", lanczos},
	{"box", box},
}

var box = &draw.Kernel{Support: 0.5, At: func(float64) float64 { return 1 }}

var lanczos = &draw.Kernel{Support: 3, At: func(t float64) float64 {
	if t == 0 {
		return 1
	}
	x := math.Pi * t
	return 3 * math.Sin(x) * math.Sin(x/3) / (x * x)
}}

// Mitchell-Netravali with B = C = 1/3.
var mitchell = &draw.Kernel{Support: 2, At: func(t float64) float64 {
	if t < 1 {
		return (7*t*t*t - 12*t*t + 16.0/3) / 6
	}
	return (-7.0/3*t*t*t + 12*t*t - 20*t + 32.0/3) / 6
}}

func methodNames() []string {
	names := make([]string, len(methods))
	for i, m := range methods {
		names[i] = m.name
	}
	return names
}

func lookupMethods(names []string) ([]method, error) {
	picked := make([]method, 0, len(names))
	for _, name := range names {
		i := slices.IndexFunc(methods, func(m method) bool { return m.name == name })
		if i < 0 {
			return nil, fmt.Errorf("unknown method %q (available: %s)", name, strings.Join(methodNames(), ", "))
		}
		picked = append(picked, methods[i])
	}
	return picked, nil
}
