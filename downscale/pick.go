package main

import (
	"errors"

	"github.com/charmbracelet/huh"
)

func pickMethods() ([]method, error) {
	options := huh.NewOptions(methodNames()...)
	for i := range options {
		options[i] = options[i].Selected(true)
	}
	var names []string
	err := huh.NewMultiSelect[string]().
		Title("Resampling methods").
		Description("space to toggle, enter to confirm").
		Options(options...).
		Value(&names).
		Validate(func(s []string) error {
			if len(s) == 0 {
				return errors.New("select at least one method")
			}
			return nil
		}).
		Run()
	if err != nil {
		return nil, err
	}
	return lookupMethods(names)
}
