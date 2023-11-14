all: sol
	time -p ./sol

sol: solve.cpp
	g++ -std=c++20 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -I ../../cpp solve.cpp -O3 -o sol
