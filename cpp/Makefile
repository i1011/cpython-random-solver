all: solver test

solver: gauss_elim.cpp
	g++ -std=c++17 -Wall -Wextra -Wpedantic -Wconversion -Wshadow gauss_elim.cpp -O3 -g -o solver

test:
	python3 gen.py > out.txt
	time -f "%E" ./solver < out.txt
