NAME=report
BIB=references.bib
.PHONY: check-bibliography sort-bibliography all

all:
	latexmk -bibtex -pdf $(NAME) --jobname=$(NAME)-final -output-directory=build
	cp -f "build/$(NAME)-final.pdf" "$(NAME).pdf"

clean:
	latexmk -C $(NAME)
	rm -rf build build-draft
	rm -f $(NAME).{aux,log,out,pdf,bbl}
