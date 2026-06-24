# human-llm-comparison
This repository includes the code for the two games and analysis files for the project FMG-19516.

# Code and analysis files

The code + analyses folder contains the analysis and game engine code files used for the project. Inside the code folder, you can find the code to initiate both games.

After downloading the repository, open the code folder in your Python terminal. Then run the relevant command below. Depending on your Python installation, use either python or python3.

Pac-Man-like game

To run the Pac-Man-like game with explicit rules:

python3 level1.py

To run the Pac-Man-like game with implicit rules:

python3 level1.py --implicit
Language reasoning game

To run the language game for the low, medium, and high complexity levels:

python language_game.py

To run the language game at maximum complexity:

python language_game.py --mode maximum

If python3 does not work on your system, try replacing it with python.
